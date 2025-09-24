import json
import sqlite3
import struct
import uuid
import zlib
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'records.db'

FONT_CANDIDATES = [
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    '/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf',
    '/Library/Fonts/AppleGothic.ttf',
    '/Library/Fonts/NotoSansKR-Regular.otf',
]


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON;')
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            date TEXT NOT NULL,
            payload TEXT NOT NULL,
            meta TEXT NOT NULL,
            evaluation TEXT 
        )
        '''
    )
    conn.commit()
    return conn


_CONN = _connect()


def _row_to_record(row: sqlite3.Row) -> Dict:
    record = {
        'id': row['id'],
        'type': row['type'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'date': row['date'],
        'payload': json.loads(row['payload']) if row['payload'] else None,
        'meta': json.loads(row['meta']) if row['meta'] else None,
    }
    # evaluation 컬럼이 존재하고, 값이 있을 때만 파싱합니다.
    if 'evaluation' in row.keys() and row['evaluation']:
        record['evaluation'] = json.loads(row['evaluation'])
    else:
        record['evaluation'] = None
        
    return record


def save_record(
    record_type: str,
    payload: Dict,
    meta: Optional[Dict] = None,
    evaluation: Optional[Dict] = None, 
    *,
    record_id: Optional[str] = None,
    created_at: Optional[str] = None,
    date: Optional[str] = None,
) -> Dict:
    now = _now_iso()
    rec_id = record_id or str(uuid.uuid4())
    cur = _CONN.execute('SELECT created_at, date, meta FROM records WHERE id = ?', (rec_id,))
    existing = cur.fetchone()

    if existing:
        created = existing['created_at']
        day = existing['date']
        existing_meta = json.loads(existing['meta'])
    else:
        created = created_at or now
        day = date or created[:10]
        existing_meta = {}

    meta_data = meta if meta is not None else existing_meta
    meta_json = json.dumps(meta_data, ensure_ascii=False)
    payload_json = json.dumps(payload, ensure_ascii=False)
    # evaluation 데이터를 JSON 문자열로 변환합니다.
    evaluation_json = json.dumps(evaluation, ensure_ascii=False) if evaluation else None

    _CONN.execute(
        '''
        INSERT INTO records (id, type, created_at, updated_at, date, payload, meta, evaluation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            type = excluded.type,
            updated_at = excluded.updated_at,
            date = excluded.date,
            payload = excluded.payload,
            meta = excluded.meta,
            evaluation = excluded.evaluation
        ''',
        (rec_id, record_type, created, now, day, payload_json, meta_json, evaluation_json),
    )
    _CONN.commit()
    cur = _CONN.execute('SELECT * FROM records WHERE id = ?', (rec_id,))
    return _row_to_record(cur.fetchone())


def save_questions_record(
    items: List[Dict],
    meta: Optional[Dict] = None,
    source_text: str = '',
    evaluation_results: Optional[Dict] = None, # 1. evaluation_results 파라미터 추가
    *,
    record_id: Optional[str] = None,
    created_at: Optional[str] = None,
    date: Optional[str] = None,
) -> Dict:
    payload = {'items': items}
    if source_text:
        payload['source_text'] = source_text
    # 2. save_record 함수를 호출할 때 evaluation_results를 함께 전달
    return save_record(
        'questions',
        payload,
        meta=meta,
        evaluation=evaluation_results, # 이 줄이 추가되었습니다.
        record_id=record_id,
        created_at=created_at,
        date=date
    )


def save_discussion_record(
    history: List[Dict],
    initial_questions: List[str],
    meta: Optional[Dict] = None,
    source_text: str = '',
    *,
    record_id: Optional[str] = None,
) -> Dict:
    payload = {
        'history': history,
        'initial_questions': initial_questions,
    }
    if source_text:
        payload['source_text'] = source_text
    elif record_id:
        existing = get_record(record_id)
        if existing:
            prev_source = existing.get('payload', {}).get('source_text')
            if prev_source:
                payload['source_text'] = prev_source
    return save_record('discussion', payload, meta=meta, record_id=record_id)


def list_records(date: Optional[str] = None) -> List[Dict]:
    if date:
        cur = _CONN.execute(
            'SELECT id, type, created_at, updated_at, date, meta FROM records WHERE date = ? ORDER BY updated_at DESC',
            (date,),
        )
    else:
        cur = _CONN.execute('SELECT id, type, created_at, updated_at, date, meta FROM records ORDER BY updated_at DESC')
    rows = cur.fetchall()
    results: List[Dict] = []
    for row in rows:
        meta = json.loads(row['meta']) if row['meta'] else {}
        results.append({
            'id': row['id'],
            'type': row['type'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'date': row['date'],
            'meta': meta,
            'title': meta.get('title'),
        })
    return results


def get_record(record_id: str) -> Optional[Dict]:
    cur = _CONN.execute('SELECT * FROM records WHERE id = ?', (record_id,))
    row = cur.fetchone()
    if not row:
        return None
    return _row_to_record(row)


def _wrap_lines(text: str, width: int = 92) -> List[str]:
    import textwrap

    wrapper = textwrap.TextWrapper(width=width, expand_tabs=False, replace_whitespace=False, drop_whitespace=False)
    lines: List[str] = []
    for raw_line in text.splitlines():
        if not raw_line:
            lines.append('')
            continue
        wrapped = wrapper.wrap(raw_line)
        if not wrapped:
            lines.append('')
            continue
        lines.extend(wrapped)
    return lines


def _record_to_lines(record: Dict) -> List[str]:
    lines: List[str] = []
    meta = record.get('meta') or {}
    payload = record.get('payload') or {}

    lines.append(f"Record ID: {record.get('id')}")
    lines.append(f"Created At (UTC): {record.get('created_at')}")
    lines.append(f"Updated At (UTC): {record.get('updated_at')}")
    lines.append(f"Date: {record.get('date')}")
    lines.append(f"Type: {record.get('type')}")

    if meta.get('title'):
        lines.append(f"Title: {meta.get('title')}")
    if meta.get('url'):
        lines.append(f"Source URL: {meta.get('url')}")
    if meta.get('language'):
        lines.append(f"Language: {meta.get('language')}")
    if meta.get('summary'):
        lines.append('Summary:')
        lines.extend(_wrap_lines(meta.get('summary')))
    if meta.get('topics'):
        topics = meta.get('topics')
        if isinstance(topics, list) and topics:
            lines.append('Topics: ' + ', '.join(map(str, topics)))

    lines.append('')

    if record.get('type') == 'questions':
        lines.append('Questions & Answers:')
        for idx, item in enumerate(payload.get('items', []), start=1):
            q = item.get('question') or ''
            a = item.get('answer') or ''
            lines.extend(_wrap_lines(f"{idx}. {q}"))
            if a:
                lines.extend(_wrap_lines(f"   Answer: {a}"))
            else:
                lines.append('   Answer: (empty)')
            lines.append('')
        if payload.get('source_text'):
            lines.append('Source Text Snippet:')
            lines.extend(_wrap_lines(payload.get('source_text')))
    elif record.get('type') == 'discussion':
        lines.append('Discussion History:')
        for entry in payload.get('history', []):
            role = (entry.get('role') or 'unknown').upper()
            content = entry.get('content') or ''
            lines.extend(_wrap_lines(f"{role}: {content}"))
            lines.append('')
        if payload.get('initial_questions'):
            lines.append('Initial Questions:')
            for idx, question in enumerate(payload.get('initial_questions', []), start=1):
                lines.extend(_wrap_lines(f"{idx}. {question}"))
    else:
        lines.append(json.dumps(payload, ensure_ascii=False, indent=2))

    return lines


def _read_tables(font_bytes: bytes) -> Dict[str, tuple]:
    num_tables = struct.unpack('>H', font_bytes[4:6])[0]
    tables: Dict[str, tuple] = {}
    offset = 12
    for _ in range(num_tables):
        tag = font_bytes[offset:offset + 4].decode('ascii', errors='ignore')
        table_offset, length = struct.unpack('>II', font_bytes[offset + 8:offset + 16])
        tables[tag] = (table_offset, length)
        offset += 16
    return tables


def _parse_cmap(font_bytes: bytes, tables: Dict[str, tuple]) -> Dict[int, int]:
    cmap_offset, cmap_length = tables.get('cmap', (0, 0))
    if not cmap_length:
        return {}
    cmap_data = font_bytes[cmap_offset:cmap_offset + cmap_length]
    num_subtables = struct.unpack('>H', cmap_data[2:4])[0]
    best_subtable = None
    for i in range(num_subtables):
        platform_id, encoding_id, sub_offset = struct.unpack('>HHI', cmap_data[4 + i * 8: 12 + i * 8])
        subtable_offset = cmap_offset + sub_offset
        fmt = struct.unpack('>H', font_bytes[subtable_offset:subtable_offset + 2])[0]
        if platform_id == 3 and encoding_id in (1, 10, 0) and fmt in (4, 12):
            best_subtable = (fmt, subtable_offset)
            if fmt == 12:
                break
    if not best_subtable:
        return {}
    fmt, subtable_offset = best_subtable
    if fmt == 4:
        return _parse_cmap_format4(font_bytes, subtable_offset)
    if fmt == 12:
        return _parse_cmap_format12(font_bytes, subtable_offset)
    return {}


def _parse_cmap_format4(font_bytes: bytes, offset: int) -> Dict[int, int]:
    cmap: Dict[int, int] = {}
    subtable_length = struct.unpack('>H', font_bytes[offset + 2:offset + 4])[0]
    subtable_end = offset + subtable_length
    seg_count = struct.unpack('>H', font_bytes[offset + 6:offset + 8])[0] // 2
    end_offset = offset + 14
    start_offset = end_offset + 2 * seg_count + 2
    delta_offset = start_offset + 2 * seg_count
    range_offset = delta_offset + 2 * seg_count
    for i in range(seg_count):
        end_code = struct.unpack('>H', font_bytes[end_offset + 2 * i:end_offset + 2 * i + 2])[0]
        start_code = struct.unpack('>H', font_bytes[start_offset + 2 * i:start_offset + 2 * i + 2])[0]
        id_delta = struct.unpack('>h', font_bytes[delta_offset + 2 * i:delta_offset + 2 * i + 2])[0]
        id_range_offset = struct.unpack('>H', font_bytes[range_offset + 2 * i:range_offset + 2 * i + 2])[0]
        for code_point in range(start_code, end_code + 1):
            if id_range_offset == 0:
                glyph_id = (code_point + id_delta) & 0xFFFF
            else:
                roffset = range_offset + 2 * i
                offset_within = id_range_offset + 2 * (code_point - start_code)
                glyph_index_offset = roffset + offset_within
                if glyph_index_offset + 2 > subtable_end:
                    glyph_id = 0
                else:
                    glyph_id = struct.unpack('>H', font_bytes[glyph_index_offset:glyph_index_offset + 2])[0]
                    if glyph_id != 0:
                        glyph_id = (glyph_id + id_delta) & 0xFFFF
            if glyph_id:
                cmap[code_point] = glyph_id
    return cmap


def _parse_cmap_format12(font_bytes: bytes, offset: int) -> Dict[int, int]:
    cmap: Dict[int, int] = {}
    subtable_length = struct.unpack('>I', font_bytes[offset + 4:offset + 8])[0]
    subtable_end = offset + subtable_length
    n_groups = struct.unpack('>I', font_bytes[offset + 12:offset + 16])[0]
    pos = offset + 16
    for _ in range(n_groups):
        if pos + 12 > subtable_end:
            break
        start_char, end_char, start_gid = struct.unpack('>III', font_bytes[pos:pos + 12])
        for code_point in range(start_char, end_char + 1):
            cmap[code_point] = start_gid + (code_point - start_char)
        pos += 12
    return cmap


def _parse_font(font_bytes: bytes) -> Dict[str, object]:
    tables = _read_tables(font_bytes)
    cmap = _parse_cmap(font_bytes, tables)
    head_offset, head_length = tables.get('head', (0, 0))
    head = font_bytes[head_offset:head_offset + head_length]
    units_per_em = struct.unpack('>H', head[18:20])[0] or 1000
    x_min, y_min, x_max, y_max = struct.unpack('>hhhh', head[36:44])

    hhea_offset, hhea_length = tables.get('hhea', (0, 0))
    hhea = font_bytes[hhea_offset:hhea_offset + hhea_length]
    ascent, descent = struct.unpack('>hh', hhea[4:8])
    num_long_metrics = struct.unpack('>H', hhea[34:36])[0]

    maxp_offset, maxp_length = tables.get('maxp', (0, 0))
    maxp = font_bytes[maxp_offset:maxp_offset + maxp_length]
    num_glyphs = struct.unpack('>H', maxp[4:6])[0]

    os2_offset, os2_length = tables.get('OS/2', (0, 0))
    cap_height = None
    if os2_offset and os2_length >= 90:
        os2 = font_bytes[os2_offset:os2_offset + os2_length]
        version = struct.unpack('>H', os2[0:2])[0]
        if version >= 2 and os2_length >= 90:
            cap_height = struct.unpack('>h', os2[88:90])[0]

    hmtx_offset, hmtx_length = tables.get('hmtx', (0, 0))
    advances: List[int] = []
    if hmtx_length:
        pos = hmtx_offset
        for _ in range(num_long_metrics):
            advance, _lsb = struct.unpack('>HH', font_bytes[pos:pos + 4])
            advances.append(advance)
            pos += 4
        last_advance = advances[-1] if advances else units_per_em
        while len(advances) < num_glyphs:
            advances.append(last_advance)
    else:
        advances = [units_per_em] * max(1, num_glyphs)

    glyph_widths = [int(round((advance or units_per_em) * 1000 / units_per_em)) for advance in advances]

    font_bbox = [
        int(x_min * 1000 / units_per_em),
        int(y_min * 1000 / units_per_em),
        int(x_max * 1000 / units_per_em),
        int(y_max * 1000 / units_per_em),
    ]

    ascent_1000 = int(ascent * 1000 / units_per_em)
    descent_1000 = int(descent * 1000 / units_per_em)
    cap_height_1000 = int((cap_height if cap_height is not None else ascent * 0.7) * 1000 / units_per_em)

    return {
        'cmap': cmap,
        'units_per_em': units_per_em,
        'glyph_widths': glyph_widths,
        'font_bbox': font_bbox,
        'ascent': ascent_1000,
        'descent': descent_1000,
        'cap_height': cap_height_1000,
    }


@lru_cache(maxsize=1)
def _load_font() -> Dict[str, object]:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if not path.exists():
            continue
        font_bytes = path.read_bytes()
        try:
            meta = _parse_font(font_bytes)
        except Exception:
            continue
        meta['font_bytes'] = font_bytes
        meta['font_name'] = 'EmbeddedGothic'
        meta['path'] = path
        return meta
    raise RuntimeError('font_not_found')


def _build_width_array(width_map: Dict[int, int]) -> str:
    if not width_map:
        return '[]'
    parts: List[str] = []
    sorted_glyphs = sorted(width_map.keys())
    start = sorted_glyphs[0]
    prev = start
    current = [width_map[start]]
    for gid in sorted_glyphs[1:]:
        if gid == prev + 1:
            current.append(width_map[gid])
        else:
            parts.append(f"{start} [{' '.join(str(w) for w in current)}]")
            start = gid
            current = [width_map[gid]]
        prev = gid
    parts.append(f"{start} [{' '.join(str(w) for w in current)}]")
    return '[' + ' '.join(parts) + ']'


def _build_tounicode(mapping: Dict[int, str]) -> bytes:
    lines: List[str] = [
        '/CIDInit /ProcSet findresource begin',
        '12 dict begin',
        'begincmap',
        '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
        '/CMapName /Adobe-Identity-UCS def',
        '/CMapType 2 def',
        '1 begincodespacerange',
        '<0000> <FFFF>',
        'endcodespacerange',
    ]

    items = sorted(mapping.items())
    chunk: List[str] = []
    for code, text in items:
        unicode_hex = ''.join(f"{ord(ch):04X}" for ch in text)
        chunk.append(f"<{code:04X}> <{unicode_hex}>")
        if len(chunk) == 100:
            lines.append(f"{len(chunk)} beginbfchar")
            lines.extend(chunk)
            lines.append('endbfchar')
            chunk = []
    if chunk:
        lines.append(f"{len(chunk)} beginbfchar")
        lines.extend(chunk)
        lines.append('endbfchar')

    lines.extend([
        'endcmap',
        'CMapName currentdict /CMap defineresource pop',
        'end',
        'end',
    ])
    return '\n'.join(lines).encode('utf-8')


def _generate_pdf(lines: List[str]) -> bytes:
    font_info = _load_font()
    cmap: Dict[int, int] = font_info['cmap']  # type: ignore
    glyph_widths: List[int] = font_info['glyph_widths']  # type: ignore

    fallback_gid = cmap.get(ord('?'), 0)
    used_glyphs = {fallback_gid, 0}
    glyph_to_unicode: Dict[int, str] = {}
    encoded_lines: List[str] = []

    for line in lines:
        glyph_ids: List[int] = []
        if not line:
            encoded_lines.append('')
            continue
        for char in line:
            gid = cmap.get(ord(char), fallback_gid)
            if gid >= len(glyph_widths):
                gid = fallback_gid
            glyph_ids.append(gid)
            used_glyphs.add(gid)
            glyph_to_unicode.setdefault(gid, char)
        encoded_lines.append(''.join(f"{gid:04X}" for gid in glyph_ids))

    if fallback_gid not in glyph_to_unicode:
        glyph_to_unicode[fallback_gid] = '?'

    width_map: Dict[int, int] = {}
    for gid in used_glyphs:
        if gid >= len(glyph_widths):
            continue
        width = glyph_widths[gid] or 500
        width_map[gid] = width
    width_array = _build_width_array(width_map)
    default_width = width_map.get(cmap.get(ord(' '), 0), 1000) or 1000

    to_unicode_stream = _build_tounicode(glyph_to_unicode)

    content_segments = []
    y_start = 812
    leading = 16
    current_y = y_start
    for encoded in encoded_lines:
        if current_y < 72:
            break
        content_segments.append(f"BT /F1 12 Tf 72 {current_y} Td <{encoded}> Tj ET")
        current_y -= leading
    content_stream = '\n'.join(content_segments).encode('ascii')

    font_descriptor = (
        "7 0 obj\n"
        f"<< /Type /FontDescriptor /FontName /{font_info['font_name']} "
        f"/Flags 4 /ItalicAngle 0 /Ascent {font_info['ascent']} "
        f"/Descent {font_info['descent']} /CapHeight {font_info['cap_height']} "
        f"/StemV 80 /FontBBox [{' '.join(str(v) for v in font_info['font_bbox'])}] "
        f"/FontFile2 9 0 R >>\n"
        "endobj\n"
    )

    descendant_font = (
        "6 0 obj\n"
        "<< /Type /Font /Subtype /CIDFontType2 "
        f"/BaseFont /{font_info['font_name']} "
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
        f"/FontDescriptor 7 0 R /W {width_array} /DW {default_width} "
        "/CIDToGIDMap /Identity >>\n"
        "endobj\n"
    )

    font_object = (
        "5 0 obj\n"
        f"<< /Type /Font /Subtype /Type0 /BaseFont /{font_info['font_name']} "
        "/Encoding /Identity-H /DescendantFonts [6 0 R] /ToUnicode 8 0 R >>\n"
        "endobj\n"
    )

    objects: List[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        (
            "3 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            "endobj\n"
        ).encode('utf-8'),
        b''
    ]
    objects[3] = (
        f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode('ascii') +
        content_stream +
        b"\nendstream\nendobj\n"
    )
    objects.append(font_object.encode('utf-8'))
    objects.append(descendant_font.encode('utf-8'))
    objects.append(font_descriptor.encode('utf-8'))

    to_unicode_bytes = _build_tounicode(glyph_to_unicode)
    objects.append(
        f"8 0 obj\n<< /Length {len(to_unicode_bytes)} >>\nstream\n".encode('ascii') +
        to_unicode_bytes +
        b"\nendstream\nendobj\n"
    )

    font_bytes = font_info['font_bytes']  # type: ignore
    compressed_font = zlib.compress(font_bytes)
    objects.append(
        f"9 0 obj\n<< /Length {len(compressed_font)} /Length1 {len(font_bytes)} /Filter /FlateDecode >>\nstream\n".encode('ascii') +
        compressed_font +
        b"\nendstream\nendobj\n"
    )

    output = bytearray()
    output.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)

    xref_pos = len(output)
    count = len(offsets)
    output.extend(f"xref\n0 {count}\n".encode('ascii'))
    output.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        output.extend(f"{off:010d} 00000 n \n".encode('ascii'))
    output.extend(
        "trailer\n"
        f"<< /Size {count} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_pos}\n"
        "%%EOF\n".encode('ascii')
    )
    return bytes(output)


def _pdf_escape(text: str) -> str:
    return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def _generate_simple_pdf(lines: List[str]) -> bytes:
    content_lines = []
    y_start = 812
    leading = 16
    current_y = y_start
    for line in lines:
        if current_y < 72:
            break
        ascii_line = line.encode('ascii', 'ignore').decode('ascii', errors='ignore')
        content_lines.append(f"BT /F1 12 Tf 72 {current_y} Td ({_pdf_escape(ascii_line)}) Tj ET")
        current_y -= leading

    content_stream = '\n'.join(content_lines).encode('ascii')
    objects: List[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        (
            "3 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            "endobj\n"
        ).encode('utf-8'),
        (
            f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode('ascii') +
            content_stream +
            b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    output = bytearray()
    output.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)

    xref_pos = len(output)
    count = len(offsets)
    output.extend(f"xref\n0 {count}\n".encode('ascii'))
    output.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        output.extend(f"{off:010d} 00000 n \n".encode('ascii'))
    output.extend(
        "trailer\n"
        f"<< /Size {count} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_pos}\n"
        "%%EOF\n".encode('ascii')
    )
    return bytes(output)


def record_to_pdf(record: Dict) -> bytes:
    lines = _record_to_lines(record)
    try:
        return _generate_pdf(lines)
    except RuntimeError:
        return _generate_simple_pdf(lines)


def records_to_pdf(record_ids: List[str]) -> bytes:
    lines: List[str] = []
    valid = 0
    for rid in record_ids:
        record = get_record(rid)
        if not record:
            continue
        valid += 1
        title = record.get('meta', {}).get('title') or ''
        header = f"=== Record: {rid}" + (f" · {title}" if title else '')
        lines.append(header)
        lines.append('')
        lines.extend(_record_to_lines(record))
        lines.append('')
    if not valid:
        raise ValueError('no_records')
    try:
        return _generate_pdf(lines)
    except RuntimeError:
        return _generate_simple_pdf(lines)
