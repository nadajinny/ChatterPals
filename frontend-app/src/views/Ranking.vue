<template>
  <main class="ranking" aria-live="polite">
    <section class="hero">
      <h1>Ranking</h1>
      <p class="lead">레벨 테스트 결과와 학습량을 기준으로 상위 학습자를 보여줍니다.</p>
      <p class="note">각 영역 월간 1위에게는 🏆 트로피가 수여됩니다.</p>
    </section>

    <section class="champions" aria-label="이달의 챔피언" v-if="levelChampion || questionChampion || discussionChampion">
      <article v-if="levelChampion" class="champion-card">
        <h3>레벨 테스트 챔피언</h3>
        <p class="name">🏆 {{ levelChampion.nickname }}</p>
        <p class="stat">최고 점수 {{ levelChampion.best_score.toFixed(1) }}%</p>
        <p class="stat muted">마지막 응시 {{ formatDate(levelChampion.last_attempt) }}</p>
      </article>
      <article v-if="questionChampion" class="champion-card">
        <h3>질문·답변 챔피언</h3>
        <p class="name">🏆 {{ questionChampion.nickname }}</p>
        <p class="stat">문항 수 {{ questionChampion.count.toLocaleString() }}개</p>
        <p class="stat muted">마지막 활동 {{ formatDate(questionChampion.last_activity) }}</p>
      </article>
      <article v-if="discussionChampion" class="champion-card">
        <h3>토론 챔피언</h3>
        <p class="name">🏆 {{ discussionChampion.nickname }}</p>
        <p class="stat">토론 수 {{ discussionChampion.count.toLocaleString() }}회</p>
        <p class="stat muted">마지막 활동 {{ formatDate(discussionChampion.last_activity) }}</p>
      </article>
    </section>

    <section class="section" aria-labelledby="level-ranking-title">
      <div class="section-head">
        <h2 id="level-ranking-title">레벨 테스트 랭킹</h2>
        <p class="hint">최고 점수 기준으로 순위를 측정했습니다.</p>
      </div>
      <table class="ranking-table">
        <thead>
          <tr>
            <th scope="col">순위</th>
            <th scope="col">닉네임</th>
            <th scope="col">최고 점수</th>
            <th scope="col">응시 횟수</th>
            <th scope="col">마지막 응시</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!levelTest.length">
            <td colspan="5" class="empty">아직 레벨 테스트 기록이 없습니다.</td>
          </tr>
          <tr v-for="entry in levelTest" :key="entry.rank">
            <td>{{ entry.rank }}</td>
            <td class="nickname-cell">
              <span
                v-if="entry.rank === 1"
                class="winner-badge"
                aria-label="이번 달 1위"
                title="이번 달 1위"
              >🥇</span>
              {{ entry.nickname }}
            </td>
            <td>{{ entry.best_score.toFixed(1) }}%</td>
            <td>{{ entry.attempts.toLocaleString() }}</td>
            <td>{{ formatDate(entry.last_attempt) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="section" aria-labelledby="question-ranking-title">
      <div class="section-head">
        <h2 id="question-ranking-title">질문·답변 랭킹</h2>
        <p class="hint">작성한 문항 수가 많은 순으로 순위를 측정했습니다.</p>
      </div>
      <table class="ranking-table">
        <thead>
          <tr>
            <th scope="col">순위</th>
            <th scope="col">닉네임</th>
            <th scope="col">문항 수</th>
            <th scope="col">마지막 활동</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!questionRanking.length">
            <td colspan="4" class="empty">아직 질문 기록이 없습니다.</td>
          </tr>
          <tr v-for="entry in questionRanking" :key="entry.rank">
            <td>{{ entry.rank }}</td>
            <td class="nickname-cell">
              <span
                v-if="entry.rank === 1"
                class="winner-badge"
                aria-label="이번 달 1위"
                title="이번 달 1위"
              >🥇</span>
              {{ entry.nickname }}
            </td>
            <td>{{ entry.count.toLocaleString() }}</td>
            <td>{{ formatDate(entry.last_activity) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="section" aria-labelledby="discussion-ranking-title">
      <div class="section-head">
        <h2 id="discussion-ranking-title">토론 랭킹</h2>
        <p class="hint">완료한 토론 세션 수를 기준으로 순위를 측정했습니다.</p>
      </div>
      <table class="ranking-table">
        <thead>
          <tr>
            <th scope="col">순위</th>
            <th scope="col">닉네임</th>
            <th scope="col">토론 수</th>
            <th scope="col">마지막 활동</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!discussionRanking.length">
            <td colspan="4" class="empty">아직 토론 기록이 없습니다.</td>
          </tr>
          <tr v-for="entry in discussionRanking" :key="entry.rank">
            <td>{{ entry.rank }}</td>
            <td class="nickname-cell">
              <span
                v-if="entry.rank === 1"
                class="winner-badge"
                aria-label="이번 달 1위"
                title="이번 달 1위"
              >🥇</span>
              {{ entry.nickname }}
            </td>
            <td>{{ entry.count.toLocaleString() }}</td>
            <td>{{ formatDate(entry.last_activity) }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchRankings, type LevelTestRankingEntry, type LearningRankingEntry } from '@/services/rankings'

const loading = ref(false)
const error = ref('')
const levelTest = ref<LevelTestRankingEntry[]>([])
const questionRanking = ref<LearningRankingEntry[]>([])
const discussionRanking = ref<LearningRankingEntry[]>([])

const levelChampion = computed(() => levelTest.value[0] ?? null)
const questionChampion = computed(() => questionRanking.value[0] ?? null)
const discussionChampion = computed(() => discussionRanking.value[0] ?? null)

onMounted(async () => {
  loading.value = true
  try {
    const data = await fetchRankings(20)
    levelTest.value = data.level_test
    questionRanking.value = data.learning.questions
    discussionRanking.value = data.learning.discussions
  } catch (err) {
    error.value = err instanceof Error ? err.message : '랭킹을 불러오지 못했습니다.'
    console.error(err)
  } finally {
    loading.value = false
  }
})

function formatDate(value?: string | null) {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('ko', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch (error) {
    return value
  }
}
</script>

<style scoped>
.ranking {
  padding: clamp(24px, 5vw, 48px);
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.hero h1 {
  margin: 0;
  font-size: clamp(2.2rem, 1.6rem + 2vw, 3rem);
  font-weight: 800;
}

.lead {
  margin-top: 0.5rem;
  color: #4b5563;
}

.note {
  margin: 0.35rem 0 0;
  color: #2563eb;
  font-weight: 500;
}

.champions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.champion-card {
  background: linear-gradient(135deg, #4f46e5, #0ea5e9);
  color: #fff;
  border-radius: 18px;
  padding: 1.25rem;
  box-shadow: 0 22px 50px rgba(14, 116, 144, 0.22);
  display: grid;
  gap: 0.45rem;
}

.champion-card h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.champion-card .name {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
}

.champion-card .stat {
  margin: 0;
  font-weight: 600;
}

.champion-card .stat.muted {
  font-weight: 500;
  opacity: 0.85;
}

.section {
  background: #ffffff;
  border-radius: 20px;
  padding: clamp(18px, 4vw, 28px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.1);
}

.section-head {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
}

.section-head h2 {
  margin: 0;
  font-size: clamp(1.5rem, 1.2rem + 1vw, 2rem);
  font-weight: 700;
}

.hint {
  margin: 0;
  color: #6b7280;
  font-size: 0.95rem;
}

.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.ranking-table thead {
  background: #f1f5f9;
}

.ranking-table th,
.ranking-table td {
  padding: 0.75rem 0.9rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.nickname-cell {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.winner-badge {
  font-size: 1.15rem;
}

.ranking-table td.nickname-cell {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.winner-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.ranking-table tbody tr:nth-child(even) {
  background: #f8fafc;
}

.empty {
  text-align: center;
  padding: 1.5rem 0;
  color: #6b7280;
}

@media (max-width: 720px) {
  .ranking {
    padding: 20px;
  }

  .ranking-table {
    font-size: 0.85rem;
  }

  .ranking-table th,
  .ranking-table td {
    padding: 0.6rem;
  }
}
</style>
