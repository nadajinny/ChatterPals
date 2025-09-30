<template>
  <main class="level-test" aria-live="polite">
    <div v-if="tipVisible && stage === 'intro'" class="tip-overlay" role="dialog" aria-modal="true">
      <div class="tip-card">
        <h3>오늘의 단어 암기</h3>
        <h3>문제를 생성중입니다.</h3>
        <h3>생성되는동안 오늘의 단어를 외워보세요!</h3>
        <ul>
          <li v-for="item in wordTips" :key="item.word">
            <strong>{{ item.word }}</strong>
            <span>— {{ item.meaning }}</span>
          </li>
          <li v-if="!wordTips.length" class="placeholder">단어를 불러오는 중...</li>
        </ul>
      </div>
    </div>

    <section v-if="stage === 'intro'" class="intro" aria-labelledby="level-test-title">
      <div class="intro-inner">
        <h1 id="level-test-title">영어 레벨 테스트</h1>
        <p class="lead">
          25개의 객관식 문항으로 문법 · 어휘 · 읽기 능력을 확인하고, CEFR 기준 레벨을 안내해 드립니다.
          질문은 매번 무작위로 섞이며, 로그인 상태라면 결과가 자동 저장됩니다.
        </p>
        <ul class="steps">
          <li>1. <strong>시작하기</strong> 버튼을 누르면 테스트 문항이 로드됩니다.</li>
          <li>2. 모든 문항을 선택한 뒤 <strong>채점하기</strong>를 누르세요.</li>
          <li>3. 총점과 영역별 분석, 추천 학습 방향을 확인합니다.</li>
        </ul>
        <button class="primary" type="button" @click="beginTest" :disabled="loading">
          {{ loading ? '문항 불러오는 중…' : '테스트 시작하기' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </section>

    <section v-else-if="stage === 'test'" class="test" aria-labelledby="test-progress">
      <header class="test-header">
        <h2 id="test-progress">문항을 모두 선택해주세요</h2>
        <p>
          총 {{ questions.length }}문항 · 현재 {{ answeredCount }}개 선택
        </p>
        <button class="link" type="button" @click="cancelTest">← 돌아가기</button>
      </header>
      <p v-if="testMode === 'static'" class="mode-hint">
        현재는 준비된 문제 은행에서 문항을 불러왔어요. 잠시 후 다시 시도하면 새 문항이 생성됩니다.
      </p>

      <form class="question-list" @submit.prevent="submitTest">
        <article v-for="(question, index) in questions" :key="question.id" class="question-card">
          <header class="question-head">
            <span class="badge">{{ index + 1 }}</span>
            <span class="skill">{{ translateSkill(question.skill) }}</span>
            <span class="level">{{ question.level }}</span>
          </header>
          <p v-if="question.passage" class="passage">{{ question.passage }}</p>
          <p class="prompt">{{ question.prompt }}</p>
          <div class="options">
            <label
              v-for="option in question.options"
              :key="option.id"
              class="option"
              :class="{ selected: selectedAnswers[question.id] === option.id }"
            >
              <input
                type="radio"
                :name="question.id"
                :value="option.id"
                v-model="selectedAnswers[question.id]"
                required
              />
              <span class="option-id">{{ option.id }}.</span>
              <span class="option-text">{{ option.text }}</span>
            </label>
          </div>
        </article>

        <footer class="actions">
          <p class="hint" v-if="!allAnswered">
            모든 문항에 답변해야 채점할 수 있습니다.
          </p>
          <button class="primary" type="submit" :disabled="submitting || !allAnswered">
            {{ submitting ? '채점 중…' : '채점하기' }}
          </button>
        </footer>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
    </section>

    <section v-else-if="stage === 'result'" class="result" aria-labelledby="result-title">
      <header class="result-head">
        <h2 id="result-title">나의 레벨: {{ evaluation?.level ?? '-' }}</h2>
        <p class="score">{{ evaluation?.feedback?.score_text }}</p>
        <p class="summary">{{ evaluation?.feedback?.summary }}</p>
        <p v-if="evaluation?.feedback?.recommendation" class="recommend">
          {{ evaluation?.feedback?.recommendation }}
        </p>
        <div class="overview">
          <div>
            <span class="number">{{ evaluation?.total_correct }}</span>
            <span class="label">정답 수</span>
          </div>
          <div>
            <span class="number">{{ evaluation?.percentage }}%</span>
            <span class="label">정답률</span>
          </div>
        </div>
        <div v-if="recordId" class="saved">
          기록이 저장되었습니다 · ID: <code>{{ recordId.slice(0, 8) }}</code>
        </div>
      </header>

      <section class="skills" v-if="skillEntries.length">
        <h3>영역별 진단</h3>
        <ul>
          <li v-for="entry in skillEntries" :key="entry.skill">
            <div class="skill-row">
              <span class="skill-name">{{ translateSkill(entry.skill) }}</span>
              <span class="skill-score">{{ entry.correct }} / {{ entry.total }} ({{ entry.percentage }}%)</span>
            </div>
            <div class="bar">
              <div class="fill" :style="{ width: entry.percentage + '%' }"></div>
            </div>
          </li>
        </ul>
      </section>

      <section class="details" v-if="details.length">
        <h3>문항 해설</h3>
        <ol>
          <li v-for="item in details" :key="item.id" :class="{ correct: item.is_correct, wrong: !item.is_correct }">
            <header>
              <span class="skill">{{ translateSkill(item.skill) }}</span>
              <span class="result-tag">{{ item.is_correct ? '정답' : '오답' }}</span>
            </header>
            <p v-if="item.passage" class="passage">{{ item.passage }}</p>
            <p class="prompt">{{ item.prompt }}</p>
            <ul class="option-list" v-if="item.options?.length">
              <li v-for="option in item.options" :key="option.id" :class="{
                    chosen: option.id === item.selected,
                    answer: option.id === item.correct,
                  }">
                <strong>{{ option.id }}.</strong> {{ option.text }}
              </li>
            </ul>
            <p class="explain">정답: {{ item.correct }} · 나의 선택: {{ item.selected || '-' }}</p>
            <p class="explain" v-if="item.explanation">{{ item.explanation }}</p>
          </li>
        </ol>
      </section>

      <footer class="result-actions">
        <button class="secondary" type="button" @click="beginTest">다시 풀기</button>
        <button class="link" type="button" @click="goStudyLog">Study Log로 이동</button>
      </footer>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import {
  startLevelTest,
  submitLevelTest,
  type LevelTestQuestion,
  type LevelTestEvaluation,
  type LevelTestResponseItem,
  fetchWordTips,
  type WordTip,
} from '@/services/levelTest'

const router = useRouter()
const { token, ensureLoaded } = useAuth()

const stage = ref<'intro' | 'test' | 'result'>('intro')
const loading = ref(false)
const submitting = ref(false)
const error = ref('')

const questions = ref<LevelTestQuestion[]>([])
const selectedAnswers = reactive<Record<string, string>>({})
const evaluation = ref<LevelTestEvaluation | null>(null)
const details = ref<LevelTestSubmitResponse['details']>([])
const recordId = ref<string | null>(null)
const sessionId = ref<string>('')
const testMode = ref<'dynamic' | 'static'>('dynamic')
const tipVisible = ref(false)
const wordTips = ref<WordTip[]>([])
const prefetchedWords = ref<WordTip[]>([])

type LevelTestSubmitResponse = Awaited<ReturnType<typeof submitLevelTest>>

async function beginTest() {
  error.value = ''
  evaluation.value = null
  details.value = []
  recordId.value = null
  stage.value = 'intro'
  loading.value = true
  sessionId.value = ''
  tipVisible.value = true
  wordTips.value = prefetchedWords.value.slice()
  try {
    await ensureLoaded()
    const [words, data] = await Promise.all([
      fetchWordTips(4).catch(() => prefetchedWords.value.slice()),
      startLevelTest(25, 'dynamic'),
    ])
    wordTips.value = (words as WordTip[]) ?? prefetchedWords.value.slice()
    prefetchedWords.value = wordTips.value.slice()
    sessionId.value = data.session_id
    testMode.value = data.mode
    questions.value = data.questions
    Object.keys(selectedAnswers).forEach((key) => delete selectedAnswers[key])
    questions.value.forEach((question) => {
      selectedAnswers[question.id] = ''
    })
    stage.value = 'test'
  } catch (err) {
    console.error(err)
    error.value = err instanceof Error ? err.message : '문항을 불러오지 못했습니다.'
    tipVisible.value = false
  } finally {
    loading.value = false
  }
}

function cancelTest() {
  stage.value = 'intro'
  error.value = ''
  sessionId.value = ''
  tipVisible.value = false
}

const answeredCount = computed(() =>
  questions.value.filter((question) => selectedAnswers[question.id]).length,
)

const allAnswered = computed(() => answeredCount.value === questions.value.length)

async function submitTest() {
  if (!allAnswered.value || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const payload: LevelTestResponseItem[] = questions.value.map((question) => ({
      question_id: question.id,
      answer: selectedAnswers[question.id],
    }))
    const response = await submitLevelTest(payload, token.value ?? undefined, sessionId.value || undefined)
    evaluation.value = response.evaluation
    details.value = response.details
    recordId.value = response.record_id ?? null
    stage.value = 'result'
    sessionId.value = ''
  } catch (err) {
    console.error(err)
    error.value = err instanceof Error ? err.message : '채점 중 오류가 발생했습니다.'
  } finally {
    submitting.value = false
    tipVisible.value = false
  }
}

function closeTip() {
  tipVisible.value = false
}

onMounted(async () => {
  prefetchedWords.value = await fetchWordTips(4).catch(() => [])
})

const skillEntries = computed(() => {
  if (!evaluation.value) return []
  return Object.entries(evaluation.value.skill_breakdown).map(([skill, stat]) => ({
    skill,
    correct: stat.correct,
    total: stat.total,
    percentage: stat.percentage,
  }))
})

function translateSkill(skill: string) {
  if (skill === 'grammar') return '문법'
  if (skill === 'vocabulary') return '어휘'
  if (skill === 'reading') return '읽기'
  return skill
}

function goStudyLog() {
  router.push('/studylog')
}
</script>

<style scoped>
.level-test {
  min-height: 100vh;
  background: linear-gradient(180deg, #f6f7ff 0%, #ffffff 60%);
  padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 56px);
}

.intro {
  max-width: 880px;
  margin: 0 auto;
  text-align: center;
}

.intro-inner {
  background: #ffffff;
  padding: clamp(24px, 4vw, 48px);
  border-radius: 24px;
  box-shadow: 0 28px 65px rgba(79, 70, 229, 0.14);
}

.intro h1 {
  margin: 0 0 1rem;
  font-size: clamp(2.2rem, 1.5rem + 2.8vw, 3.6rem);
  font-weight: 800;
  color: #1f2937;
}

.lead {
  color: #4b5563;
  font-size: 1.1rem;
  line-height: 1.7;
  margin-bottom: 1.5rem;
}

.steps {
  text-align: left;
  list-style: decimal;
  padding-left: 1.4rem;
  color: #374151;
  margin-bottom: 2rem;
}

.primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.85rem 1.75rem;
  border-radius: 999px;
  background: #4f46e5;
  color: #fff;
  font-weight: 700;
  border: none;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  color: #dc2626;
}

.test {
  max-width: 960px;
  margin: 0 auto;
}

.test-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.test-header h2 {
  margin: 0;
  font-size: clamp(1.5rem, 1.1rem + 1.1vw, 2rem);
}

.link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-weight: 600;
}

.tip {
  background: rgba(15, 23, 42, 0.08);
  border-left: 4px solid #4f46e5;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  white-space: pre-line;
  color: #1f2937;
}

.mode-hint {
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  color: #0f172a;
}

.tip-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.tip-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 1.5rem;
  width: min(90vw, 360px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
  display: grid;
  gap: 1rem;
  white-space: pre-line;
  color: #1f2937;
}

.tip-card h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.tip-card p {
  margin: 0;
  line-height: 1.55;
}

.tip-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.4rem;
}

.tip-card li {
  display: flex;
  gap: 0.5rem;
  font-weight: 500;
}

.tip-card li span {
  font-weight: 400;
  color: #475569;
}

.tip-card li.placeholder {
  font-weight: 400;
  color: #6b7280;
}

.tip-close {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.6rem 1.2rem;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #4f46e5, #0ea5e9);
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
}

.tip-close:hover {
  opacity: 0.9;
}

.question-list {
  display: grid;
  gap: clamp(16px, 2.4vw, 24px);
}

.question-card {
  background: #ffffff;
  border-radius: 18px;
  padding: clamp(18px, 2.6vw, 28px);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(79, 70, 229, 0.1);
}

.question-head {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.badge {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #4f46e5;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.skill {
  font-weight: 600;
  color: #4338ca;
}

.level {
  margin-left: auto;
  color: #6b7280;
  font-size: 0.9rem;
}

.passage {
  background: rgba(79, 70, 229, 0.06);
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.prompt {
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.options {
  display: grid;
  gap: 0.5rem;
}

.option {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.8rem;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  cursor: pointer;
}

.option:hover {
  border-color: #4f46e5;
}

.option.selected {
  border-color: #4f46e5;
  background: rgba(79, 70, 229, 0.08);
}

.option input {
  margin: 0;
}

.option-id {
  font-weight: 700;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1rem;
}

.hint {
  color: #6b7280;
}

.result {
  max-width: 960px;
  margin: 0 auto;
  display: grid;
  gap: 2rem;
}

.result-head {
  background: #111827;
  border-radius: 24px;
  padding: clamp(24px, 3vw, 40px);
  color: #fff;
  box-shadow: 0 32px 70px rgba(15, 23, 42, 0.3);
}

.result-head h2 {
  margin: 0 0 0.5rem;
  font-size: clamp(2rem, 1.5rem + 1.8vw, 3rem);
}

.score {
  margin: 0 0 0.5rem;
  font-weight: 700;
}

.summary, .recommend {
  margin: 0 0 1rem;
  line-height: 1.6;
}

.overview {
  display: flex;
  gap: 1.5rem;
  margin-top: 1rem;
}

.overview .number {
  display: block;
  font-size: 1.8rem;
  font-weight: 800;
}

.overview .label {
  color: rgba(255, 255, 255, 0.7);
}

.saved {
  margin-top: 1.5rem;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.8);
}

.skills ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1rem;
}

.skill-row {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
}

.bar {
  width: 100%;
  height: 10px;
  border-radius: 6px;
  background: rgba(79, 70, 229, 0.15);
  overflow: hidden;
}

.bar .fill {
  height: 100%;
  background: #4f46e5;
  border-radius: inherit;
}

.details ol {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1.2rem;
}

.details li {
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 18px;
  padding: 1.25rem;
  background: #fff;
}

.details li.correct {
  border-color: rgba(16, 185, 129, 0.4);
}

.details li.wrong {
  border-color: rgba(239, 68, 68, 0.4);
}

.result-tag {
  margin-left: auto;
  font-weight: 700;
  color: #16a34a;
}

.details li.wrong .result-tag {
  color: #dc2626;
}

.option-list {
  list-style: none;
  padding: 0;
  margin: 0.75rem 0;
  display: grid;
  gap: 0.5rem;
}

.option-list li {
  display: flex;
  gap: 0.5rem;
}

.option-list li.answer {
  font-weight: 700;
}

.option-list li.chosen:not(.answer) {
  color: #dc2626;
}

.explain {
  margin: 0.3rem 0;
  color: #4b5563;
}

.result-actions {
  display: flex;
  gap: 1rem;
}

.secondary {
  background: none;
  border: 1px solid #4f46e5;
  color: #4f46e5;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  cursor: pointer;
}

@media (max-width: 720px) {
  .overview {
    flex-direction: column;
    align-items: flex-start;
  }
  .result-actions {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .level-test {
    padding: 20px 14px 40px;
  }

  .intro-inner {
    padding: 24px 18px;
  }

  .question-head {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .question-card {
    padding: 18px 16px;
  }

  .options {
    gap: 0.4rem;
  }

  .option {
    align-items: flex-start;
  }

  .option-id {
    min-width: 20px;
  }

  .actions {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .primary {
    width: 100%;
    justify-content: center;
  }

  .result {
    gap: 1.5rem;
  }

  .skills ul {
    gap: 0.75rem;
  }

  .level-responses {
    padding: 1.1rem;
  }
}
</style>
