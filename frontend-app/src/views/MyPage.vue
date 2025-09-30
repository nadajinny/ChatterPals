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
      class="daily-goal"
      aria-live="polite"
    >
      <header class="goal-header">
        <h3>일일 학습 목표</h3>
        <button
          type="button"
          class="goal-refresh"
          @click="loadDailyGoal"
          :disabled="goalLoading || goalSaving"
        >
          {{ goalLoading ? '불러오는 중...' : '새로고침' }}
        </button>
      </header>

      <p v-if="goalError" class="goal-error">{{ goalError }}</p>

      <div class="goal-body">
        <form class="goal-form" @submit.prevent="saveGoal">
          <label class="goal-field">
            <span>질문·답변 목표</span>
            <div class="field-control">
              <input
                type="number"
                min="0"
                max="999"
                v-model.number="goalForm.questions_target"
                :disabled="goalSaving"
                aria-describedby="goal-question-help"
              />
              <span class="unit">개</span>
            </div>
            <small id="goal-question-help">오늘 {{ dailyGoal?.questions_completed ?? 0 }}개 진행</small>
          </label>
          <label class="goal-field">
            <span>토론 목표</span>
            <div class="field-control">
              <input
                type="number"
                min="0"
                max="999"
                v-model.number="goalForm.discussions_target"
                :disabled="goalSaving"
                aria-describedby="goal-discussion-help"
              />
              <span class="unit">회</span>
            </div>
            <small id="goal-discussion-help">오늘 {{ dailyGoal?.discussions_completed ?? 0 }}회 진행</small>
          </label>
          <button type="submit" class="goal-save" :disabled="goalSaving">
            {{ goalSaving ? '저장 중...' : '목표 저장' }}
          </button>
        </form>

        <div class="goal-status" v-if="dailyGoal">
          <div class="progress-group">
            <div class="progress-item">
              <p class="progress-label">질문·답변</p>
              <div
                class="progress-bar"
                role="progressbar"
                :aria-valuenow="goalProgress.questionsPercent"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <span class="progress-fill" :style="{ width: goalProgress.questionsPercent + '%' }"></span>
              </div>
              <p class="progress-value">{{ dailyGoal.questions_completed }} / {{ dailyGoal.questions_target }}</p>
            </div>
            <div class="progress-item">
              <p class="progress-label">토론</p>
              <div
                class="progress-bar"
                role="progressbar"
                :aria-valuenow="goalProgress.discussionsPercent"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <span class="progress-fill secondary" :style="{ width: goalProgress.discussionsPercent + '%' }"></span>
              </div>
              <p class="progress-value">{{ dailyGoal.discussions_completed }} / {{ dailyGoal.discussions_target }}</p>
            </div>
          </div>

          <div class="goal-reward" :class="{ unlocked: dailyGoal.achieved }">
            <div class="goal-stamp" aria-hidden="true">
              <span v-if="dailyGoal.achieved">🏆</span>
              <span v-else>📘</span>
            </div>
            <div class="reward-text">
              <strong v-if="dailyGoal.achieved">오늘의 목표를 달성했어요!</strong>
              <span v-if="dailyGoal.achieved && dailyGoal.achieved_at"> {{ formatDate(dailyGoal.achieved_at) }} 도장 지급</span>
              <span v-else>목표를 채우면 오늘의 도장이 발급돼요.</span>
            </div>
          </div>
        </div>
      </div>

      <div class="goal-history-block">
        <h4>최근 도장 기록</h4>
        <p v-if="goalHistoryError" class="goal-error">{{ goalHistoryError }}</p>
        <p v-else-if="goalHistoryLoading" class="goal-note">불러오는 중...</p>
        <p v-else-if="!goalHistory.length" class="goal-note">아직 도장이 없어요. 오늘 목표부터 달성해 볼까요?</p>
        <ul v-else class="goal-history">
          <li v-for="item in goalHistory" :key="item.goal_date">
            <span class="history-date">{{ formatDate(item.achieved_at) }}</span>
            <span class="history-target">Q {{ item.questions_target }} · 토론 {{ item.discussions_target }}</span>
          </li>
        </ul>
      </div>
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
import { computed, onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { deleteMyRecord, fetchMyRecords, fetchMyRankings, type MyRecord, type MyRankingsResponse } from '@/services/auth'
import { fetchDailyGoal, fetchDailyGoalHistory, saveDailyGoal, type DailyGoal, type DailyGoalHistoryItem } from '@/services/dailyGoals'

const router = useRouter()
const { user, token, isAuthenticated, ensureLoaded } = useAuth()
const records = ref<MyRecord[]>([])
const loading = ref(false)
const error = ref('')
const activeFilter = ref<'all' | 'questions' | 'discussion' | 'level_test'>('all')
const rankingLoading = ref(false)
const rankingError = ref('')
const myRankings = ref<MyRankingsResponse | null>(null)
const dailyGoal = ref<DailyGoal | null>(null)
const goalForm = reactive({
  questions_target: 0,
  discussions_target: 0,
})
const goalLoading = ref(false)
const goalSaving = ref(false)
const goalError = ref('')
const goalHistoryLoading = ref(false)
const goalHistoryError = ref('')
const goalHistory = ref<DailyGoalHistoryItem[]>([])

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

function sanitizeTarget(value: number) {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(999, Math.round(value)))
}

function syncGoalForm(goal: DailyGoal | null) {
  goalForm.questions_target = sanitizeTarget(goal?.questions_target ?? 0)
  goalForm.discussions_target = sanitizeTarget(goal?.discussions_target ?? 0)
}

async function loadDailyGoal() {
  if (!token.value) return
  goalLoading.value = true
  goalError.value = ''
  try {
    const data = await fetchDailyGoal(token.value)
    dailyGoal.value = data
    syncGoalForm(data)
  } catch (err) {
    console.error(err)
    goalError.value = err instanceof Error ? err.message : '일일 목표를 불러오지 못했습니다.'
  } finally {
    goalLoading.value = false
  }
}

async function loadGoalHistory() {
  if (!token.value) return
  goalHistoryLoading.value = true
  goalHistoryError.value = ''
  try {
    goalHistory.value = await fetchDailyGoalHistory(token.value, 10)
  } catch (err) {
    console.error(err)
    goalHistoryError.value = err instanceof Error ? err.message : '도장 기록을 불러오지 못했습니다.'
  } finally {
    goalHistoryLoading.value = false
  }
}

async function saveGoal() {
  if (!token.value) return
  goalSaving.value = true
  goalError.value = ''
  const payload = {
    questions_target: sanitizeTarget(goalForm.questions_target),
    discussions_target: sanitizeTarget(goalForm.discussions_target),
  }
  goalForm.questions_target = payload.questions_target
  goalForm.discussions_target = payload.discussions_target
  try {
    const updated = await saveDailyGoal(token.value, payload)
    dailyGoal.value = updated
    syncGoalForm(updated)
    await loadGoalHistory()
  } catch (err) {
    console.error(err)
    goalError.value = err instanceof Error ? err.message : '일일 목표를 저장하지 못했습니다.'
  } finally {
    goalSaving.value = false
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
    loadDailyGoal()
    loadGoalHistory()
  }
  window.addEventListener('chatter-records-updated', handleRecordsUpdated)
})

watch(isAuthenticated, (val) => {
  if (val) {
    loadRecords()
    loadRankingSummary()
    loadDailyGoal()
    loadGoalHistory()
  } else {
    records.value = []
    myRankings.value = null
    dailyGoal.value = null
    goalHistory.value = []
    goalError.value = ''
    goalHistoryError.value = ''
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

const goalProgress = computed(() => {
  if (!dailyGoal.value) {
    return { questionsPercent: 0, discussionsPercent: 0 }
  }
  const { questions_target, questions_completed, discussions_target, discussions_completed } = dailyGoal.value
  const questionsPercent = questions_target > 0 ? Math.min(100, Math.round((questions_completed / questions_target) * 100)) : 0
  const discussionsPercent = discussions_target > 0 ? Math.min(100, Math.round((discussions_completed / discussions_target) * 100)) : 0
  return { questionsPercent, discussionsPercent }
})

function handleRecordsUpdated() {
  if (!isAuthenticated.value) return
  loadRecords()
  loadRankingSummary()
  loadDailyGoal()
  loadGoalHistory()
}

onBeforeUnmount(() => {
  window.removeEventListener('chatter-records-updated', handleRecordsUpdated)
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

.daily-goal {
  max-width: 960px;
  margin: 0 auto 2.5rem;
  padding: clamp(18px, 4vw, 28px);
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.goal-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.goal-refresh {
  border: 1px solid #2563eb;
  color: #2563eb;
  background: transparent;
  padding: 0.35rem 0.9rem;
  border-radius: 9999px;
  cursor: pointer;
}

.goal-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.goal-error {
  color: #dc2626;
  margin: 0;
  font-size: 0.95rem;
}

.goal-note {
  color: #4b5563;
  margin: 0;
  font-size: 0.95rem;
}

.goal-body {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  align-items: start;
}

.goal-form {
  display: grid;
  gap: 1rem;
  background: #f9fafb;
  border-radius: 16px;
  padding: 1.25rem;
}

.goal-field {
  display: grid;
  gap: 0.45rem;
  font-weight: 600;
  color: #1f2937;
}

.field-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 0.35rem 0.75rem;
}

.field-control input[type='number'] {
  flex: 1;
  border: none;
  font-size: 1rem;
  padding: 0.25rem 0;
  background: transparent;
  outline: none;
}

.field-control .unit {
  color: #6b7280;
  font-size: 0.95rem;
}

.goal-field small {
  color: #6b7280;
  font-weight: 500;
}

.goal-save {
  border: none;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  font-weight: 700;
  border-radius: 12px;
  padding: 0.65rem 1rem;
  cursor: pointer;
}

.goal-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.goal-status {
  display: grid;
  gap: 1.2rem;
  background: #f9fafb;
  border-radius: 16px;
  padding: 1.25rem;
}

.progress-group {
  display: grid;
  gap: 1rem;
}

.progress-item {
  display: grid;
  gap: 0.4rem;
}

.progress-label {
  margin: 0;
  font-weight: 600;
  color: #1f2937;
}

.progress-bar {
  position: relative;
  width: 100%;
  height: 12px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  position: absolute;
  inset: 0;
  width: 0;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.8), rgba(14, 165, 233, 0.8));
  border-radius: inherit;
  transition: width 0.3s ease;
}

.progress-fill.secondary {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.8), rgba(59, 130, 246, 0.8));
}

.progress-value {
  margin: 0;
  font-size: 0.95rem;
  color: #374151;
}

.goal-reward {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 16px;
  border: 2px dashed rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.06);
  transition: transform 0.25s ease;
}

.goal-reward.unlocked {
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(16, 185, 129, 0.08);
  transform: translateY(-2px);
}

.goal-stamp {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 2rem;
  background: #fff;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
}

.goal-reward.unlocked .goal-stamp {
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
}

.reward-text {
  display: grid;
  gap: 0.3rem;
  color: #1f2937;
}

.reward-text strong {
  font-size: 1.05rem;
  color: #065f46;
}

.goal-history-block {
  display: grid;
  gap: 0.6rem;
}

.goal-history-block h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #111827;
}

.goal-history {
  list-style: none;
  display: grid;
  gap: 0.6rem;
  padding: 0;
  margin: 0;
}

.goal-history li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  color: #1f2937;
}

.history-date {
  font-weight: 600;
  color: #2563eb;
}

.history-target {
  color: #4b5563;
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
