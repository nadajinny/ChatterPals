<template>

  <main class="screen" aria-label="Chatterpals 소개">
    <!-- 콘텐츠: 위젯 전환 전 -->
    <div v-if="!hasStarted" class="content">
      <!-- 히어로 -->
      <header class="intro" aria-labelledby="p1-title">
        <p class="eyebrow">Welcome</p>
        <h1 id="p1-title" class="title">Chatterpals에 대해서 소개할게요</h1>
        <p class="subtitle">친구와 대화하듯 자연스럽게 배우는 AI 튜터</p>
        <div class="hero-cta">
          <button class="btn-primary" @click="hasStarted = true">지금 시작하기</button>
          <a href="#how" class="btn-link">어떻게 동작하나요?</a>
        </div>
      </header>

      <!-- 문제점 -->
      <section class="block" aria-labelledby="prob-title">
        <h2 id="prob-title" class="section-title">기존 영어 학습의 문제점</h2>
        <ul class="chat" aria-label="기존 영어 학습의 문제점">
          <li class="bubble left">
            <span class="icon" aria-hidden="true">😕</span>
            <p>너무 정형화되어 있어요. 매번 똑같아서 실력이 늘고 있는지 모르겠어요.</p>
          </li>
          <li class="bubble left">
            <span class="icon" aria-hidden="true">💬</span>
            <p>조금 더 평상시에 친구와 대화하듯 이야기하고 싶어요.</p>
          </li>
          <li class="bubble left">
            <span class="icon" aria-hidden="true">💸</span>
            <p>원어민 튜터는 가격이 높아서 부담이 돼요.</p>
          </li>
        </ul>
      </section>

      <!-- 해결법 -->
      <section class="block" aria-labelledby="sol-title">
        <h2 id="sol-title" class="section-title right">Chatterpals가 생각한 해결법</h2>
        <ul class="chat" aria-label="Chatterpals의 해결 방법">
          <li class="bubble right">
            <span class="icon" aria-hidden="true">📱</span>
            <p>항상 쓰는 휴대폰에서, 언제든 대화를 이어가자.</p>
          </li>
          <li class="bubble right">
            <span class="icon" aria-hidden="true">🧭</span>
            <p>주제를 다양하게 다뤄 여러 상황에서 말해볼 수 있게 하자.</p>
          </li>
          <li class="bubble right">
            <span class="icon" aria-hidden="true">📘</span>
            <p>대화 기록을 바탕으로 교본/피드백을 제공해 지속적으로 성장하자.</p>
          </li>
        </ul>
      </section>

            <!-- 사용 흐름 -->
      <section id="how" class="how" aria-labelledby="how-title">
        <h2 id="how-title" class="section-title center">어떻게 동작하나요?</h2>
        <ol class="steps" aria-label="사용 흐름 3단계">
          <li>
            <span class="step-icon" aria-hidden="true">🧪</span>
            <h3>레벨 파악</h3>
            <p>간단한 진단 대화로 현재 수준과 목표를 설정해요.</p>
          </li>
          <li>
            <span class="step-icon" aria-hidden="true">🎯</span>
            <h3>주제 선택</h3>
            <p>관심사/상황별 주제로 대화를 이어가며 실전 감각을 길러요.</p>
          </li>
          <li>
            <span class="step-icon" aria-hidden="true">📈</span>
            <h3>피드백 & 교본</h3>
            <p>대화 기록 기반으로 표현·발음·문법 피드백을 받아요.</p>
          </li>
        </ol>
      </section>


      <!-- 숫자 하이라이트 -->
      <section class="stats" aria-label="성과/하이라이트">
        <h2 id="stats-title" class="section-title center">현재까지의 성과</h2>
        <ul class="stats__list">
          <li><strong>92%</strong><span>1주 내 발화 자신감 향상*</span></li>
          <li><strong>50K+</strong><span>누적 대화 세션</span></li>
          <li><strong>4.8/5</strong><span>사용자 만족도</span></li>
        </ul>
        <p class="stats__footnote">* 내부 베타 테스트 기준</p>
      </section>


      <!-- FAQ -->
      <section id="faq" class="faq-wrap" aria-labelledby="faq-title">
        <h2 id="faq-title" class="section-title center">자주 묻는 질문</h2>
        <div class="faq-list">
          <details class="faq">
            <summary class="faq__q">무료로 체험할 수 있나요?</summary>
            <p class="faq__a">네, 회원가입만 하면 기본 기능을 무료로 이용할 수 있어요.</p>
          </details>
          <details class="faq">
            <summary class="faq__q">개인정보/대화 데이터는 안전한가요?</summary>
            <p class="faq__a">대화는 암호화되어 저장되며, 설정에서 언제든 삭제할 수 있어요.</p>
          </details>
          <details class="faq">
            <summary class="faq__q">모바일에서도 사용할 수 있나요?</summary>
            <p class="faq__a">네, 모바일 웹/데스크톱 모두 최적화되어 있어요.</p>
          </details>
        </div>
      </section>

      <!-- 하단 CTA -->
      <section class="cta-band" aria-label="시작 CTA">
        <div class="cta-band__inner">
          <div class="cta-band__text">
            <h2>바로 시작해볼까요?</h2>
            <p>한 번의 클릭으로, 나에게 맞춘 대화를 바로 경험하세요.</p>
          </div>
          <button class="btn-primary lg" @click="hasStarted = true">지금 시작하기</button>
        </div>
      </section>

      <!-- 푸터 -->
      <footer class="footer" aria-label="푸터">
        <div class="footer__inner">
          <span>© {{ new Date().getFullYear() }} Chatterpals</span>
          <nav class="footer__nav">
            <a href="/legal/privacy">개인정보처리방침</a>
            <a href="/legal/terms">이용약관</a>
            <a href="mailto:hello@chatterpals.app">문의</a>
          </nav>
        </div>
      </footer>
    </div>

    <!-- 콘텐츠: 위젯 전환 후 -->
    <div v-else class="content">
      <AITutorWidget />
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AITutorWidget from '@/components/AITutorWidget.vue'
const hasStarted = ref(false)
</script>

<style scoped>
/* ========== Topbar ========== */
.topbar{ position: sticky; top: 0; z-index: 10; backdrop-filter: blur(6px) saturate(110%); }
.topbar__inner{
  width: min(1100px, 96vw); margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0;
}
.brand{ color:#fff; font-weight:900; letter-spacing:.2px; }
.topbar__actions{ display:flex; align-items:center; gap:12px; }
.link{ color:#e5e7eb; font-weight:600; text-decoration:none; }
.link:hover{ opacity:.9; }
.btn-ghost{
  padding:.6rem .9rem; border-radius:10px; background:rgba(255,255,255,.14);
  color:#fff; font-weight:800; border:1px solid rgba(255,255,255,.25); cursor:pointer;
}
.btn-ghost:hover{ background:rgba(255,255,255,.2); }
@media (prefers-color-scheme: light){
  .brand{ color:#0f172a; } .link{ color:#1f2937; }
  .btn-ghost{ background:#111827; color:#fff; border-color:transparent; }
}

/* ========== Page & Gradient ========== */
.screen{
  position: relative;
  min-height: 100svh;
  padding: clamp(16px, 3vw, 32px) 0 clamp(40px, 6vw, 72px);
  background: #0b1220;
  overflow: initial;
}
.screen::before{
  content:"";
  position: fixed; 
  inset: 0; 
  z-index: 0;
  /* 스샷 느낌의 파스텔 그라데이션 (오렌지 → 민트 → 시안) */
  background: linear-gradient(
    var(--grad-angle),
    #f6b77d 0%,
    #cfe6b0 48%,
    #98e6f2 100%
  );


  /* 각도 회전 애니메이션 */
  animation: rotate-gradient 24s linear infinite;
  filter: saturate(1.04) blur(.3px);
  opacity:.96; pointer-events:none;
}
@keyframes grad-spin{ to{ transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce){ .screen::before{ animation:none; } }

/* ========== Content Wrapper ========== */
.content{
  position: relative; z-index:1;
  width:min(1100px, 96vw); margin: 0 auto;
  display:grid; gap: clamp(18px, 2.2vw, 28px);
}

/* ========== Hero ========== */
.intro{ display:grid; gap:10px; text-align:center; }
.eyebrow{
  font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  font-size:clamp(.7rem, .5rem + .5vw, .85rem); opacity:.9; color:#fff;
}
.title{
  font-weight:900; line-height:1.1;
  font-size:clamp(2.1rem, 1.2rem + 3.4vw, 3.3rem); margin:0; color:#0f172a;
  text-shadow: 0 1px 0 rgba(255,255,255,.35);
}
.subtitle{ font-size:clamp(1rem, .9rem + .5vw, 1.2rem); color:rgba(17,24,39,.9); margin:0; }
.hero-cta{ display:flex; gap:12px; justify-content:center; margin-top:4px; }
.btn-primary{
  padding:.9rem 1.2rem; border-radius:12px; background:#111827; color:#fff; font-weight:800;
  border:none; cursor:pointer; box-shadow:0 6px 18px rgba(17,24,39,.18);
}
.btn-primary.lg{ padding:1rem 1.4rem; border-radius:14px; }
.btn-primary:hover{ opacity:.95; box-shadow:0 8px 24px rgba(17,24,39,.24); }
.btn-link{ align-self:center; color:#0f172a; font-weight:800; text-decoration:underline; }

/* ========== Sections ========== */
.block{ width:min(900px,100%); text-align:left; margin: clamp(8px, 1.6vw, 18px) auto 0; }
.section-title{ font-size:clamp(1.2rem, .9rem + .9vw, 1.5rem); font-weight:900; margin:0 0 .5rem; color:#0f172a; }
.section-title.center{ text-align:center; }
.section-title.right {  text-align: right;}

/* ========== Chat Bubbles ========== */
.chat{ list-style:none; margin:0; padding:clamp(6px,1vw,10px) 0 0; display:grid; gap:clamp(8px,1.2vw,12px); }
.bubble{
  display:grid; grid-template-columns:auto 1fr; align-items:start; gap:8px;
  max-width:70ch;
  padding:clamp(8px,1vw,10px) clamp(10px,1.4vw,12px);
  border-radius:14px; line-height:1.45; position:relative;
  font-size:clamp(.98rem, .9rem + .35vw, 1.08rem);
  backdrop-filter:saturate(110%) blur(.4px);
}
.bubble.left  { justify-self:start; background:rgba(255,255,255,.92); color:#0f172a; }
.bubble.right { justify-self:end;   background:rgba(99,102,241,.12); color:#0f172a; border:1px solid rgba(99,102,241,.35); }
.bubble.left::after,
.bubble.right::after{
  content:""; position:absolute; bottom:-6px; width:12px; height:12px; transform:rotate(45deg);
}
.bubble.left::after  { left:18px;  background:inherit; }
.bubble.right::after { right:18px; background:inherit; border-right:inherit; border-bottom:inherit; }
.icon{ font-size:1.1em; line-height:1; margin-top:2px; }

/* ========== Stats ========== */
.stats{ text-align:center; margin-top: clamp(14px,2.5vw,28px); }
.stats__list{
  display:grid; grid-template-columns: repeat(3,1fr); gap: clamp(10px,2vw,18px);
  width:min(900px,100%); margin:0 auto; padding:0; list-style:none;
}
.stats__list li{
  background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.25);
  border-radius:14px; padding:14px; color:#fff;
}
.stats__list strong{ display:block; font-size:clamp(1.4rem,1rem + 2vw,2rem); line-height:1.1; }
.stats__list span{ opacity:.92; font-size:.95rem; }
.stats__footnote{ opacity:.8; color:#fff; margin-top:8px; font-size:.85rem; }

/* ========== How it works ========== */
.how{ margin-top: clamp(18px,3vw,36px); }
.steps{
  list-style:none; padding:0; margin:12px auto 0; width:min(900px,100%);
  display:grid; grid-template-columns: repeat(3,1fr); gap: clamp(10px,2vw,18px);
}
.steps li{
  background: rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.25);
  border-radius:16px; padding:16px; color:#fff; text-align:center;
}
.step-icon{ font-size:1.4rem; display:block; margin-bottom:6px; }
.steps h3{ margin:6px 0 4px; font-weight:900; }
.steps p{ margin:0; opacity:.95; }

/* ========== FAQ ========== */
.faq-wrap{ width:min(900px,100%); margin: clamp(18px,3vw,36px) auto 0; }
.faq-list{ display:grid; gap:10px; }
.faq{
  background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.25);
  border-radius:12px; padding:12px 14px; color:#fff;
}
.faq__q{ cursor:pointer; font-weight:900; outline:none; }
.faq__a{ margin:10px 0 0; opacity:.95; }

/* ========== CTA Band ========== */
.cta-band{ margin-top: clamp(20px, 4vw, 48px); }
.cta-band__inner{
  width:min(1100px, 96vw); margin:0 auto;
  display:grid; grid-template-columns: 1fr auto; align-items:center; gap:12px;
  background: rgba(17,24,39,.9); color:#fff; border-radius:16px; padding: clamp(12px, 2vw, 18px);
  border: 1px solid rgba(255,255,255,.15);
}
.cta-band__text h2{ margin:0; font-size: clamp(1.3rem, 1rem + 1vw, 1.7rem); }
.cta-band__text p{ margin:.2rem 0 0; opacity:.9; }

/* ========== Footer ========== */
.footer{ margin-top: clamp(24px, 4vw, 56px); }
.footer__inner{
  width:min(1100px,96vw); margin:0 auto; display:flex; justify-content:space-between; align-items:center;
  color:#fff; opacity:.9; font-size:.95rem;
}
.footer__nav{ display:flex; gap:12px; }
.footer__nav a{ color:inherit; text-decoration:none; }
.footer__nav a:hover{ text-decoration:underline; }

/* ========== Light mode ========== */
@media (prefers-color-scheme: light){
  .screen{ background:#f4f6fb; }
  .section-title, .subtitle, .btn-link{ color:#0f172a; }
  .stats__list li, .steps li, .faq{ background:#fff; border-color:#e5e7eb; color:#0f172a; }
  .stats__footnote{ color:#475569; }
  .bubble.right{ background:#eef2ff; color:#1e293b; border-color:#c7d2fe; }
  .cta-band__inner{ background:#111827; }
  .footer__inner{ color:#1f2937; }
}

/* ========== Responsive ========== */
@media (max-width: 900px){
  .steps{ grid-template-columns: 1fr; }
  .stats__list{ grid-template-columns: 1fr; }
  .cta-band__inner{ grid-template-columns: 1fr; justify-items:center; text-align:center; }
}
@media (max-width:420px){ .title{ word-break: keep-all; } }
</style>
