<template>
  <main class="mypage">
    <section class="hero" aria-labelledby="mypage-title">
      <h2 id="mypage-title">마이페이지</h2>
      <p v-if="!isAuthenticated">
        👋 학습 기록을 확인하려면 먼저 오른쪽 상단에서 <strong>로그인</strong>하거나 <strong>회원가입</strong>을 진행해 주세요.
      </p>
      <p v-else>
        {{ user?.nickname }}님, 오늘도 화이팅이에요! 아래에서 최근 질문/토론 기록을 확인하고 관리할 수 있습니다.
      </p>
    </section>

    <section
      v-if="isAuthenticated"
      class="ranking-summary"
      aria-live="polite"
    >
      <header class="ranking-header">
        <h3>나의 랭킹 요약</h3>
        <span v-if="rankingLoading" class="ranking-status">불러오는 중...</span>
        <span v-else-if="rankingError" class="ranking-status error">{{ rankingError }}</span>
      </header>
      <div class="ranking-grid">
        <article class="rank-card">
          <h4>레벨 테스트</h4>
          <p class="rank">{{ levelRankText }}</p>
          <p class="detail" v-if="myRankings?.level_test">
            최고 점수 {{ myRankings.level_test.best_score.toFixed(1) }}%,
            응시 {{ myRankings.level_test.attempts.toLocaleString() }}회
          </p>
          <p class="caption">최근: {{ myRankings?.level_test?.last_attempt ? formatDate(myRankings.level_test.last_attempt) : '-' }}</p>
        </article>
        <article class="rank-card">
          <h4>질문·답변</h4>
          <p class="rank">{{ questionRankText }}</p>
          <p class="detail" v-if="myRankings?.learning?.questions">
            작성 문항 {{ myRankings.learning.questions.count.toLocaleString() }}개
          </p>
          <p class="caption">최근: {{ myRankings?.learning?.questions?.last_activity ? formatDate(myRankings.learning.questions.last_activity) : '-' }}</p>
        </article>
        <article class="rank-card">
          <h4>토론</h4>
          <p class="rank">{{ discussionRankText }}</p>
          <p class="detail" v-if="myRankings?.learning?.discussions">
            토론 {{ myRankings.learning.discussions.count.toLocaleString() }}회
          </p>
          <p class="caption">최근: {{ myRankings?.learning?.discussions?.last_activity ? formatDate(myRankings.learning.discussions.last_activity) : '-' }}</p>
        </article>
      </div>
      <RouterLink class="ranking-link" to="/ranking">전체 랭킹 보기 →</RouterLink>
    </section>

    <section v-if="isAuthenticated" class="records" aria-live="polite">
      <header class="records-header">
        <div class="filters" role="tablist" aria-label="기록 유형 필터">
          <button
            type="button"
            :class="['filter', { active: activeFilter === 'all' }]"
            @click="setFilter('all')"
          >전체</button>
          <button
            type="button"
            :class="['filter', { active: activeFilter === 'questions' }]"
            @click="setFilter('questions')"
          >질문·답변</button>
          <button
            type="button"
            :class="['filter', { active: activeFilter === 'discussion' }]"
            @click="setFilter('discussion')"
          >토론</button>
          <button
            type="button"
            :class="['filter', { active: activeFilter === 'level_test' }]"
            @click="setFilter('level_test')"
          >레벨 테스트</button>
        </div>
        <button class="refresh" type="button" @click="loadRecords" :disabled="loading">
          {{ loading ? '불러오는 중...' : '새로고침' }}
        </button>
      </header>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-else-if="!loading && filteredRecords.length === 0" class="empty">현재 필터에 해당하는 기록이 없습니다.</p>

      <ul v-if="filteredRecords.length" class="record-grid">
        <li
          v-for="record in filteredRecords"
          :key="record.id"
          class="record-card"
          role="button"
          tabindex="0"
          @click="openRecord(record.id)"
          @keyup.enter="openRecord(record.id)"
          @keyup.space.prevent="openRecord(record.id)"
        >
          <div class="card-main">
            <p class="record-type">{{ translateType(record.type) }}</p>
            <h4>{{ record.title || '제목 없음' }}</h4>
            <p class="record-date">{{ formatDate(record.created_at) }}</p>
            <p v-if="getSummary(record.meta)" class="record-summary">{{ getSummary(record.meta) }}</p>
            <p class="detail-cta">자세히 보기 →</p>
          </div>
          <button
            class="delete"
            type="button"
            @click.stop="confirmDelete(record.id)"
            aria-label="기록 삭제"
          >삭제</button>
        </li>
      </ul>
      <RouterLink v-if="filteredRecords.length" to="/studylog" class="more-link">통계 보기</RouterLink>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { deleteMyRecord, fetchMyRecords, fetchMyRankings, type MyRecord, type MyRankingsResponse } from '@/services/auth'

const router = useRouter()
const { user, token, isAuthenticated, ensureLoaded } = useAuth()
const records = ref<MyRecord[]>([])
const loading = ref(false)
const error = ref('')
const activeFilter = ref<'all' | 'questions' | 'discussion' | 'level_test'>('all')
const rankingLoading = ref(false)
const rankingError = ref('')
const myRankings = ref<MyRankingsResponse | null>(null)

const filteredRecords = computed(() => {
  if (activeFilter.value === 'all') return records.value
  return records.value.filter((record) => record.type === activeFilter.value)
})

async function loadRecords() {
  if (!token.value) return
  loading.value = true
  error.value = ''
  try {
    records.value = await fetchMyRecords(token.value)
  } catch (err) {
    console.error(err)
    error.value = err instanceof Error ? err.message : '기록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function loadRankingSummary() {
  if (!token.value) return
  rankingLoading.value = true
  rankingError.value = ''
  try {
    myRankings.value = await fetchMyRankings(token.value)
  } catch (err) {
    console.error(err)
    rankingError.value = err instanceof Error ? err.message : '랭킹 정보를 불러오지 못했습니다.'
    myRankings.value = null
  } finally {
    rankingLoading.value = false
  }
}

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat('ko', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch (error) {
    return iso
  }
}

function translateType(type: string) {
  if (type === 'questions') return '질문·답변'
  if (type === 'discussion') return '토론'
  if (type === 'level_test') return '레벨 테스트'
  return type
}

function getSummary(meta: MyRecord['meta']) {
  if (!meta) return ''
  const maybeSummary = (meta as { summary?: unknown }).summary
  return typeof maybeSummary === 'string' ? maybeSummary : ''
}

function openRecord(id: string) {
  router.push({ name: 'RecordDetail', params: { id } })
}

function setFilter(filter: 'all' | 'questions' | 'discussion' | 'level_test') {
  activeFilter.value = filter
}

async function confirmDelete(id: string) {
  if (!token.value) return
  const sure = window.confirm('해당 학습 기록을 삭제할까요? 삭제 후에는 되돌릴 수 없습니다.')
  if (!sure) return
  try {
    await deleteMyRecord(token.value, id)
    await loadRecords()
    window.dispatchEvent(new CustomEvent('chatter-records-updated'))
  } catch (error) {
    const message = error instanceof Error ? error.message : '삭제에 실패했습니다.'
    alert(message)
  }
}

onMounted(async () => {
  await ensureLoaded()
  if (isAuthenticated.value) {
    loadRecords()
    loadRankingSummary()
  }
})

watch(isAuthenticated, (val) => {
  if (val) {
    loadRecords()
    loadRankingSummary()
  } else {
    records.value = []
    myRankings.value = null
  }
})

const levelRankText = computed(() => {
  const rank = myRankings.value?.level_test?.rank
  return rank ? `#${rank}` : '기록 없음'
})

const questionRankText = computed(() => {
  const rank = myRankings.value?.learning?.questions?.rank
  return rank ? `#${rank}` : '기록 없음'
})

const discussionRankText = computed(() => {
  const rank = myRankings.value?.learning?.discussions?.rank
  return rank ? `#${rank}` : '기록 없음'
})
</script>

<style scoped>
.mypage {
  padding: 2rem 1rem;
}

.hero {
  max-width: 900px;
  margin: 0 auto 2rem;
  text-align: center;
}

.hero h2 {
  font-size: 2.4rem;
  margin-bottom: 0.75rem;
}

.hero p {
  color: #4b5563;
  line-height: 1.6;
}

.ranking-summary {
  max-width: 960px;
  margin: 0 auto 2rem;
  padding: clamp(18px, 4vw, 28px);
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.1);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.ranking-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.ranking-status {
  font-size: 0.95rem;
  color: #2563eb;
}

.ranking-status.error {
  color: #dc2626;
}

.ranking-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.rank-card {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(14, 165, 233, 0.12));
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 16px;
  padding: 1rem 1.2rem;
  display: grid;
  gap: 0.35rem;
}

.rank-card h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
}

.rank-card .rank {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 800;
  color: #111827;
}

.rank-card .detail {
  margin: 0;
  color: #1f2937;
  font-weight: 600;
}

.rank-card .caption {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.ranking-link {
  align-self: flex-end;
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

.ranking-link:hover {
  text-decoration: underline;
}

.records {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.filters {
  display: inline-flex;
  border-radius: 999px;
  background: #f3f4f6;
  padding: 4px;
}

.filter {
  border: none;
  background: transparent;
  padding: 0.45rem 1.1rem;
  border-radius: 999px;
  font-weight: 600;
  color: #4b5563;
  cursor: pointer;
}

.filter.active {
  background: #2563eb;
  color: #fff;
}

.refresh {
  border: 1px solid #2563eb;
  color: #2563eb;
  background: transparent;
  padding: 0.35rem 0.9rem;
  border-radius: 9999px;
  cursor: pointer;
}

.refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #dc2626;
}

.empty {
  color: #6b7280;
}

.record-grid {
  list-style: none;
  display: grid;
  gap: 1.25rem;
  padding: 0;
  margin: 0;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.record-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}

.record-card:hover,
.record-card:focus-visible {
  transform: translateY(-3px);
  box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
}

.card-main {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.record-type {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6366f1;
  text-transform: uppercase;
}

.record-date {
  font-size: 0.9rem;
  color: #6b7280;
}

.record-summary {
  font-size: 0.95rem;
  color: #374151;
  line-height: 1.5;
}

.detail-cta {
  margin-top: auto;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2563eb;
}

.delete {
  align-self: flex-end;
  border: 1px solid #dc2626;
  color: #dc2626;
  background: transparent;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
  font-size: 0.85rem;
  cursor: pointer;
}

.more-link {
  align-self: flex-end;
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .hero p {
    color: #9ca3af;
  }
  .record-card {
    background: #1f2937;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.4);
  }
  .record-summary {
    color: #e5e7eb;
  }
  .record-date {
    color: #9ca3af;
  }
}
</style>
