<!-- src/views/StudyLog.vue -->
<template>
  <main class="studylog">
    <section class="hero" aria-labelledby="studylog-title">
      <h1 id="studylog-title" class="title">학습 통계</h1>

      <p v-if="!isAuthenticated" class="hint">
        학습 기록은 로그인 후 자동으로 저장됩니다. 상단에서 로그인하고 확장 프로그램에서 저장하면 이곳에 통계가 나타납니다.
      </p>

      <div v-else class="stats-wrapper" aria-live="polite">
        <button class="refresh" type="button" @click="loadRecords" :disabled="loading">
          {{ loading ? '새로고침 중...' : '새로고침' }}
        </button>
      </div>
    </section>

    <section v-if="isAuthenticated" class="stats-board" aria-live="polite">
      <p v-if="error" class="error">{{ error }}</p>
      <p v-else-if="!loading && !records.length" class="hint">아직 저장된 학습 기록이 없습니다.</p>

      <dl v-else class="stat-grid">
        <div class="stat-card">
          <dt>총 기록 수</dt>
          <dd>{{ totalRecords.toLocaleString() }}</dd>
        </div>
        <div class="stat-card">
          <dt>질문 수</dt>
          <dd>{{ totalQuestions.toLocaleString() }}</dd>
        </div>
        <div class="stat-card">
          <dt>토론 수</dt>
          <dd>{{ discussionCount.toLocaleString() }}</dd>
        </div>
        <div class="stat-card">
          <dt>평균 점수 (전체)</dt>
          <dd>
            <ul class="score-list">
              <li>문법 {{ displayScore(averageScores.all.grammar) }}</li>
              <li>어휘 {{ displayScore(averageScores.all.vocabulary) }}</li>
              <li>논리 {{ displayScore(averageScores.all.clarity) }}</li>
            </ul>
          </dd>
        </div>
        <div class="stat-card">
          <dt>평균 점수 (질문·답변)</dt>
          <dd>
            <ul class="score-list">
              <li>문법 {{ displayScore(averageScores.questions.grammar) }}</li>
              <li>어휘 {{ displayScore(averageScores.questions.vocabulary) }}</li>
              <li>논리 {{ displayScore(averageScores.questions.clarity) }}</li>
            </ul>
          </dd>
        </div>
        <div class="stat-card">
          <dt>평균 점수 (토론)</dt>
          <dd>
            <ul class="score-list">
              <li>문법 {{ displayScore(averageScores.discussion.grammar) }}</li>
              <li>어휘 {{ displayScore(averageScores.discussion.vocabulary) }}</li>
              <li>논리 {{ displayScore(averageScores.discussion.clarity) }}</li>
            </ul>
          </dd>
        </div>
        <div class="stat-card highlight" v-if="weakestArea">
          <dt>현재 약점</dt>
          <dd>{{ weakestArea }}</dd>
        </div>
      </dl>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { fetchMyRecords, fetchMyRecord, type MyRecord } from '@/services/auth'

const { isAuthenticated, token, ensureLoaded } = useAuth()
const records = ref<MyRecord[]>([])
const loading = ref(false)
const error = ref('')

const totalRecords = computed(() => records.value.length)
const discussionCount = computed(() => records.value.filter(r => r.type === 'discussion').length)

const totalQuestions = computed(() => {
  return records.value.reduce((sum, record) => {
    if (record.type !== 'questions') return sum
    const payload = record.payload as { items?: Array<{ question: string }> }
    return sum + (payload?.items?.length || 0)
  }, 0)
})

const averageScores = computed(() => {
  try {
    const defaultBucket = { grammar: 0, vocabulary: 0, clarity: 0, count: 0 }
    const buckets: Record<'all' | 'questions' | 'discussion', typeof defaultBucket> = {
      all: { ...defaultBucket },
      questions: { ...defaultBucket },
      discussion: { ...defaultBucket },
    }

    records.value.forEach((record) => {
      if (record.type === 'questions') {
        const evaluation = record.evaluation as { evaluations?: Array<{ evaluation?: { scores?: { grammar?: number; vocabulary?: number; clarity?: number } } }> } | string | null
        let items: Array<{ evaluation?: { scores?: { grammar?: number; vocabulary?: number; clarity?: number } } }> | undefined
        if (typeof evaluation === 'string') {
          try {
            const parsed = JSON.parse(evaluation)
            items = parsed?.evaluations
          } catch (error) {
            console.warn('Failed to parse question evaluation', error)
          }
        } else {
          items = evaluation?.evaluations
        }
        items?.forEach((item) => {
          const scores = item.evaluation?.scores
          if (!scores) return
          buckets.questions.grammar += scores.grammar ?? 0
          buckets.questions.vocabulary += scores.vocabulary ?? 0
          buckets.questions.clarity += scores.clarity ?? 0
          buckets.questions.count += 1
        })
      } else if (record.type === 'discussion') {
        let detail: unknown = record.evaluation
        if (typeof detail === 'string') {
          try {
            detail = JSON.parse(detail)
          } catch (error) {
            console.warn('Failed to parse discussion evaluation', error)
            detail = undefined
          }
        }
        const scores = (detail as { scores?: { grammar?: number; vocabulary?: number; clarity?: number } } | undefined)?.scores
        if (scores) {
          buckets.discussion.grammar += scores.grammar ?? 0
          buckets.discussion.vocabulary += scores.vocabulary ?? 0
          buckets.discussion.clarity += scores.clarity ?? 0
          buckets.discussion.count += 1
        }
      }
    })

    ;(['questions', 'discussion'] as const).forEach((key) => {
      const bucket = buckets[key]
      buckets.all.grammar += bucket.grammar
      buckets.all.vocabulary += bucket.vocabulary
      buckets.all.clarity += bucket.clarity
      buckets.all.count += bucket.count
    })

    const computeAverage = (bucket: typeof defaultBucket) => {
      if (!bucket.count) return { grammar: 0, vocabulary: 0, clarity: 0 }
      return {
        grammar: bucket.grammar / bucket.count,
        vocabulary: bucket.vocabulary / bucket.count,
        clarity: bucket.clarity / bucket.count,
      }
    }

    return {
      all: computeAverage(buckets.all),
      questions: computeAverage(buckets.questions),
      discussion: computeAverage(buckets.discussion),
    }
  } catch (error) {
    console.error('Failed to compute averages', error)
    return {
      all: { grammar: 0, vocabulary: 0, clarity: 0 },
      questions: { grammar: 0, vocabulary: 0, clarity: 0 },
      discussion: { grammar: 0, vocabulary: 0, clarity: 0 },
    }
  }
})

const weakestArea = computed(() => {
  const scores = averageScores.value.all
  const entries: Array<[string, number]> = [
    ['문법', scores.grammar],
    ['어휘', scores.vocabulary],
    ['논리', scores.clarity],
  ]
  const filtered = entries.filter(([, score]) => score > 0)
  if (!filtered.length) return ''
  filtered.sort((a, b) => a[1] - b[1])
  return `${filtered[0][0]} (평균 ${filtered[0][1].toFixed(1)}점)`
})

async function loadRecords() {
  if (!token.value) return
  loading.value = true
  error.value = ''
  try {
    const baseRecords = await fetchMyRecords(token.value)
    records.value = baseRecords
    if (!baseRecords.length) {
      return
    }

    const enriched: MyRecord[] = []
    for (const record of baseRecords) {
      if (record.type !== 'questions' && record.type !== 'discussion') {
        enriched.push(record)
        continue
      }
      try {
        const detail = await fetchMyRecord(token.value!, record.id)
        enriched.push({ ...record, payload: detail.payload, evaluation: detail.evaluation })
      } catch (error) {
        console.warn('Failed to load detail for record', record.id, error)
        enriched.push(record)
      }
    }
    records.value = enriched
  } catch (err) {
    console.error(err)
    error.value = err instanceof Error ? err.message : '기록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await ensureLoaded()
  if (isAuthenticated.value) {
    loadRecords()
  }
  window.addEventListener('chatter-records-updated', handleExternalUpdate)
})

watch(isAuthenticated, (value) => {
  if (value) {
    loadRecords()
  } else {
    records.value = []
  }
})

onUnmounted(() => {
  window.removeEventListener('chatter-records-updated', handleExternalUpdate)
})

function handleExternalUpdate() {
  if (isAuthenticated.value) {
    loadRecords()
  }
}

function displayScore(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '-'
  }
  return `${value.toFixed(1)} / 5`
}
</script>

<style scoped>
.studylog {
  padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px);
  max-width: 960px;
  margin: 0 auto;
}

.hero {
  margin-bottom: clamp(24px, 4vw, 40px);
}

.title {
  font-weight: 800;
  font-size: clamp(2.25rem, 1.5rem + 2.8vw, 4.25rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #111827; /* gray-900 */
  margin: 0 0 clamp(18px, 2.2vw, 26px);
}

.stats-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-bottom: clamp(20px, 3vw, 32px);
}

.refresh {
  border: 1px solid #2563eb;
  color: #2563eb;
  background: transparent;
  padding: 0.45rem 1rem;
  border-radius: 999px;
  cursor: pointer;
}

.stats-board {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: clamp(14px, 3vw, 24px);
  margin: 0;
  padding: 0;
}

.stat-card {
  list-style: none;
  background: #ffffff;
  border-radius: 18px;
  padding: clamp(16px, 3vw, 24px);
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.12);
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.stat-card dt {
  margin: 0;
  color: #6b7280;
  font-weight: 600;
  font-size: 0.95rem;
}

.stat-card dd {
  margin: 0;
  font-size: clamp(1.6rem, 1.2rem + 1.2vw, 2.2rem);
  font-weight: 700;
  color: #111827;
}

.score-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: #1f2937;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-card.highlight {
  background: linear-gradient(130deg, #1d4ed8, #0ea5e9);
  color: #fff;
  border: none;
}

.stat-card.highlight .score-list {
  color: #f9fafb;
}

.hint {
  color: #6b7280;
  margin-top: 0.5rem;
}

.error {
  color: #dc2626;
}

/* 다크 모드 */
@media (prefers-color-scheme: dark) {
  .title { color: #e5e7eb; }
  .stats strong { color: #f3f4f6; }
  .record-item { background: #111827; border-color: #1f2937; }
  .record-summary { color: #d1d5db; }
  .record-date { color: #9ca3af; }
}
</style>
