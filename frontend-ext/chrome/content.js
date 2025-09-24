// content.js
// -----------------------------------------------------------------------------
// ChatterPals Content Script
// - 페이지에 플로팅 버튼(FAB) 주입
// - 사이드바(iframe) 열기/닫기
// - popup → background → content 메시지 처리
// - 페이지/선택 텍스트 추출
// -----------------------------------------------------------------------------

(() => {
  const SIDEBAR_IFRAME_ID = 'chatterpals-sidebar-iframe';
  const FAB_ID = 'chatterpals-fab';
  const SIDEBAR_URL = chrome.runtime.getURL('popup.html?context=sidebar');

  let sidebarIframe = null;
  let fabEl = null;

  // ---------------------------
  // 초기화: 플로팅 버튼 가시성 반영
  // ---------------------------
  chrome.storage.local.get(['floatingButtonVisible'], (res) => {
    const visible = res.floatingButtonVisible !== false; // 기본 true
    updateFABVisibility(visible);
  });

  // ---------------------------
  // 플로팅 버튼
  // ---------------------------
  function injectFAB() {
    if (document.getElementById(FAB_ID)) {
      fabEl = document.getElementById(FAB_ID);
      return;
    }
    fabEl = document.createElement('button');
    fabEl.id = FAB_ID;
    fabEl.type = 'button';
    fabEl.setAttribute('aria-label', 'Open ChatterPals sidebar');
    // 시각 아이콘은 CSS background-image로 표시 → 텍스트 비움
    fabEl.textContent = '';

    fabEl.addEventListener('click', () => {
      openSidebar();
    });

    document.documentElement.appendChild(fabEl);
  }

  function removeFAB() {
    if (fabEl && fabEl.parentNode) fabEl.parentNode.removeChild(fabEl);
    fabEl = null;
  }

  function updateFABVisibility(visible) {
    if (visible) injectFAB();
    else removeFAB();
  }

  // ---------------------------
  // 사이드바
  // ---------------------------
  function openSidebar() {
    if (sidebarIframe && document.getElementById(SIDEBAR_IFRAME_ID)) {
      try { sidebarIframe.focus(); } catch {}
      return;
    }
    sidebarIframe = document.createElement('iframe');
    sidebarIframe.id = SIDEBAR_IFRAME_ID;
    sidebarIframe.src = SIDEBAR_URL;
    document.documentElement.appendChild(sidebarIframe);

    // CSS 트랜지션을 위해 다음 틱에 visible 부여
    requestAnimationFrame(() => {
      sidebarIframe?.classList.add('visible');
    });
  }

  function closeSidebar() {
    const iframe = document.getElementById(SIDEBAR_IFRAME_ID);
    if (!iframe) return;

    // 닫힐 때 슬라이드아웃
    iframe.classList.remove('visible');
    // 트랜지션 시간(약 280ms) 후 제거
    setTimeout(() => {
      if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
      sidebarIframe = null;
    }, 300);
  }

  // ---------------------------
  // 텍스트 추출
  // ---------------------------
  function getSelectionText() {
    try {
      const sel = window.getSelection ? window.getSelection().toString() : '';
      return (sel || '').trim();
    } catch {
      return '';
    }
  }

  function getFullPageText(limit = 20000) {
    let text = '';
    try {
      text = (document.body?.innerText || document.documentElement?.innerText || '').trim();
    } catch {}
    if (text.length > limit) text = text.slice(0, limit);
    return text;
  }

  // ---------------------------
  // 메시지 핸들러
  // ---------------------------
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // 팝업/백그라운드 → 컨텐츠 스크립트

    if (request.action === 'toggleFloatingButton') {
      updateFABVisibility(!!request.visible);
      sendResponse?.({ ok: true });
      return true;
    }

    if (request.action === 'getTextFromPage') {
      const type = request.type || 'selection';
      const text = type === 'fullPage' ? getFullPageText() : getSelectionText();
      sendResponse?.({ text });
      return true;
    }

    if (request.action === 'openSidebarFromContext') {
      openSidebar();
      sendResponse?.({ ok: true });
      return true;
    }

    if (request.action === 'closeSidebar') {
      // ✖ 버튼 → popup.js → background.js → (여기)
      closeSidebar();
      sendResponse?.({ status: 'sidebar closed' });
      return true;
    }

    return false;
  });

  // (선택) ESC 키로 닫기
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // (선택) 뷰포트가 아주 작을 때 FAB 위치 미세 조정 (CSS 미디어쿼리로도 처리됨)
  window.addEventListener('resize', () => {
    // CSS에서 처리하므로 빈 훅으로 유지하거나 필요 시 로직 추가
  });
})();
