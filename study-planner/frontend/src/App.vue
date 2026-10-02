<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  ArrowUpRight, BookOpen, CalendarDays, Check, Circle, Clock3, ExternalLink,
  GraduationCap, Layers3, LoaderCircle, RotateCcw, Search, Sparkles, Target
} from 'lucide-vue-next'
import { generatePlan, getCurrentPlan, updateTask } from './services/api'
import type { PlanRequest, StudyPlan, StudyTask, TaskStatus } from './types'

const learnerStorageKey = 'study-planner:learner-id'
const learnerId = ref(localStorage.getItem(learnerStorageKey) || 'my-learning-space')
const contextMode = ref<'continue' | 'independent'>('continue')
const today = new Date()
const deadlineDefault = new Date(today.getTime() + 60 * 86400000).toISOString().slice(0, 10)
const form = reactive({
  goal: '', subject: '', current_level: '初学者', weekly_hours: 6,
  study_days_per_week: 5, session_minutes: 60, deadline: deadlineDefault, context_notes: ''
})
const plan = ref<StudyPlan | null>(null)
const loading = ref(false)
const updatingTask = ref<string | null>(null)
const error = ref('')

const completedCount = computed(() => plan.value?.near_term_tasks.filter(task => task.status === 'completed').length ?? 0)
const progress = computed(() => {
  const total = plan.value?.near_term_tasks.length ?? 0
  return total ? Math.round((completedCount.value / total) * 100) : 0
})

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' }).format(new Date(`${value}T00:00:00`))
}

function formatDay(value: string) {
  const date = new Date(`${value}T00:00:00`)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function formatWeekday(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { weekday: 'short' }).format(new Date(`${value}T00:00:00`))
}

async function loadPlan() {
  try {
    plan.value = await getCurrentPlan(learnerId.value)
    if (plan.value && contextMode.value === 'continue' && !form.goal.trim()) {
      form.goal = plan.value.goal.clarified_goal
    }
  } catch {
    error.value = '无法连接到后端。请先启动 FastAPI 服务。'
  }
}

function setContextMode(mode: 'continue' | 'independent') {
  contextMode.value = mode
  if (mode === 'independent' && plan.value && form.goal === plan.value.goal.clarified_goal) {
    form.goal = ''
  }
  if (mode === 'continue' && plan.value && !form.goal.trim()) {
    form.goal = plan.value.goal.clarified_goal
  }
}

async function submitPlan() {
  if (form.goal.trim().length < 4) {
    error.value = '请先写下至少 4 个字的学习目标。'
    return
  }
  loading.value = true
  error.value = ''
  const requestLearnerId = contextMode.value === 'independent' ? crypto.randomUUID() : learnerId.value
  const payload: PlanRequest = { learner_id: requestLearnerId, ...form }
  try {
    plan.value = await generatePlan(payload)
    if (contextMode.value === 'independent') {
      learnerId.value = requestLearnerId
      localStorage.setItem(learnerStorageKey, requestLearnerId)
      contextMode.value = 'continue'
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '计划生成失败。'
  } finally {
    loading.value = false
  }
}

async function toggleTask(task: StudyTask) {
  updatingTask.value = task.id
  error.value = ''
  const nextStatus: TaskStatus = task.status === 'completed' ? 'todo' : 'completed'
  try {
    const updated = await updateTask(task.id, nextStatus)
    if (plan.value) {
      const index = plan.value.near_term_tasks.findIndex(item => item.id === updated.id)
      if (index >= 0) plan.value.near_term_tasks[index] = updated
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '任务状态更新失败。'
  } finally {
    updatingTask.value = null
  }
}

onMounted(loadPlan)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#top" aria-label="知序首页">
        <span class="brand-mark"><Layers3 :size="20" :stroke-width="2.2" /></span>
        <span class="brand-name">知序<span>STUDY STUDIO</span></span>
      </a>
      <div class="sidebar-label">工作区</div>
      <a class="nav-item active" href="#plan"><Target :size="17" />学习规划</a>
      <a class="nav-item" href="#tasks"><CalendarDays :size="17" />近期任务</a>
      <a class="nav-item" href="#resources"><BookOpen :size="17" />资料书架</a>
      <div class="sidebar-bottom">
        <div class="sidebar-note">
          <div class="note-icon"><Sparkles :size="16" /></div>
          <strong>循序渐进</strong>
          <p>把大目标拆成今天能开始的一小步。</p>
        </div>
        <div class="profile">
          <div class="avatar">知</div>
          <div><strong>我的学习空间</strong><span>个人计划</span></div>
          <ArrowUpRight :size="15" />
        </div>
      </div>
    </aside>

    <main id="top" class="main-content">
      <header class="topbar">
        <div class="breadcrumb">工作区 <span>/</span> 学习规划</div>
        <div class="topbar-right"><span class="today-dot"></span>{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }}</div>
      </header>

      <section id="plan" class="intro-row">
        <div>
          <div class="eyebrow"><span class="eyebrow-line"></span>YOUR LEARNING, IN RHYTHM</div>
          <h1>让目标，<em>开始发生。</em></h1>
          <p class="intro-copy">告诉我你想学什么。四位规划 Agent 会一起拆解目标、寻找资料，并安排下一步。</p>
        </div>
        <div class="date-stamp"><span>今天</span><strong>{{ new Date().getDate() }}</strong><small>{{ new Date().toLocaleDateString('zh-CN', { month: 'long', weekday: 'long' }) }}</small></div>
      </section>

      <section class="planner-layout">
        <form class="goal-form" @submit.prevent="submitPlan">
          <div class="form-heading">
            <div class="heading-icon"><Target :size="19" /></div>
            <div><h2>定义你的目标</h2><p>规划会根据你的节奏实时调整</p></div>
            <span class="form-step">01 <i>/ 01</i></span>
          </div>
          <label class="field-label" for="goal">我希望达成</label>
          <textarea id="goal" v-model="form.goal" rows="2" maxlength="500" placeholder="例如：三个月内掌握 Python 数据分析，并完成一个作品集项目"></textarea>
          <fieldset class="context-selector">
            <legend class="field-label">规划上下文</legend>
            <div class="context-options">
              <label class="context-option" :class="{ selected: contextMode === 'continue' }">
                <input type="radio" name="context-mode" :checked="contextMode === 'continue'" @change="setContextMode('continue')" />
                <span><strong>接续当前计划</strong><small>沿用当前学习空间的未完成任务</small></span>
              </label>
              <label class="context-option" :class="{ selected: contextMode === 'independent' }">
                <input type="radio" name="context-mode" :checked="contextMode === 'independent'" @change="setContextMode('independent')" />
                <span><strong>独立新建</strong><small>从空白开始，不读取历史任务</small></span>
              </label>
            </div>
            <p class="context-hint">{{ contextMode === 'continue' ? '会把当前学习空间的未完成任务安排到新计划中。' : '会创建独立学习空间；之前的计划会保留，但不会带入本次规划。' }}</p>
          </fieldset>
          <div class="form-grid">
            <label class="field-wrap"><span class="field-label">学习主题</span><input v-model="form.subject" placeholder="如：Python、英语、考研" /></label>
            <label class="field-wrap"><span class="field-label">当前水平</span><select v-model="form.current_level"><option>初学者</option><option>有一些基础</option><option>进阶提升</option><option>准备考试 / 项目</option></select></label>
            <label class="field-wrap"><span class="field-label">每周投入（小时）</span><input v-model.number="form.weekly_hours" type="number" min="1" max="60" /></label>
            <label class="field-wrap"><span class="field-label">每周学习天数</span><input v-model.number="form.study_days_per_week" type="number" min="1" max="7" /></label>
            <label class="field-wrap"><span class="field-label">单次时长（分钟）</span><input v-model.number="form.session_minutes" type="number" min="15" max="240" step="15" /></label>
            <label class="field-wrap"><span class="field-label">目标日期</span><input v-model="form.deadline" type="date" /></label>
          </div>
          <label class="field-wrap context-field"><span class="field-label">补充背景 <span>选填</span></span><input v-model="form.context_notes" placeholder="如：上次学到函数、周末时间更多、最近有考试" /></label>
          <div class="form-footer">
            <span class="privacy-note"><Circle :size="8" fill="currentColor" />进度保存在本地学习空间</span>
            <button class="primary-button" type="submit" :disabled="loading">
              <LoaderCircle v-if="loading" class="spin" :size="17" />
              <Sparkles v-else :size="17" />
              {{ loading ? '四位 Agent 正在协作…' : plan ? '重新生成计划' : '生成学习计划' }}
              <ArrowUpRight v-if="!loading" :size="16" />
            </button>
          </div>
        </form>

        <aside class="agent-panel">
          <div class="agent-panel-top"><span class="live-indicator"></span><span>协作系统</span><span class="agent-count">4 AGENTS</span></div>
          <h2>一个目标，<br />四种专业视角。</h2>
          <p class="agent-caption">从理解你想要什么，到把下一步排进日历。</p>
          <div class="agent-list">
            <div v-for="(agent, index) in (plan?.agents ?? [
              { name: '目标解析 Agent', status: '待启动', detail: '拆解目标与里程碑' },
              { name: '资料搜索 Agent', status: '待启动', detail: 'MCP 接入外部学习资料' },
              { name: '经验整合 Agent', status: '待启动', detail: '结合背景和过往进度' },
              { name: '规划协调 Agent', status: '待启动', detail: '安排近期与远期计划' }
            ])" :key="agent.name" class="agent-row" :style="{ '--agent-index': index }">
              <span class="agent-number">0{{ index + 1 }}</span>
              <span class="agent-info"><strong>{{ agent.name }}</strong><small>{{ agent.detail }}</small></span>
              <span class="agent-status" :class="{ done: agent.status === '完成' }">{{ agent.status === '完成' ? '就绪' : '待命' }}</span>
            </div>
          </div>
          <div class="memory-note"><RotateCcw :size="14" /><span>接续模式会带入未完成任务；独立模式从空白开始。</span></div>
        </aside>
      </section>

      <div v-if="error" class="error-banner" role="alert">{{ error }}</div>

      <template v-if="plan && contextMode === 'continue'">
        <section class="summary-strip" aria-label="计划摘要">
          <div class="summary-goal"><span class="summary-icon"><GraduationCap :size="18" /></span><div><small>当前目标</small><strong>{{ plan.goal.clarified_goal }}</strong></div></div>
          <div class="summary-stat"><span>计划周期</span><strong>{{ plan.goal.estimated_weeks }}<small>周</small></strong></div>
          <div class="summary-stat"><span>近期进度</span><strong>{{ completedCount }}<small> / {{ plan.near_term_tasks.length }}</small></strong></div>
          <div class="progress-track"><span :style="{ width: `${progress}%` }"></span></div>
        </section>

        <section class="workspace-grid">
          <div id="tasks" class="tasks-section">
            <div class="section-heading">
              <div><div class="eyebrow"><span class="eyebrow-line"></span>THE NEXT TWO WEEKS</div><h2>近期安排 <span class="heading-count">{{ plan.near_term_tasks.length }}</span></h2></div>
              <span class="detail-tag"><Clock3 :size="13" />逐日细化</span>
            </div>
            <p v-if="plan.migrated_tasks_count" class="migration-banner"><RotateCcw :size="15" />{{ plan.migrated_tasks_count }} 项未完成任务已提升优先级并安排到本周期。</p>
            <div v-if="!plan.near_term_tasks.length" class="empty-state">还没有任务，试着调整目标日期后重新生成。</div>
            <div v-for="(task, index) in plan.near_term_tasks" :key="task.id" class="task-row" :class="{ completed: task.status === 'completed' }">
              <button class="task-check" :aria-label="task.status === 'completed' ? '标记未完成' : '标记完成'" :disabled="updatingTask === task.id" @click="toggleTask(task)">
                <LoaderCircle v-if="updatingTask === task.id" class="spin" :size="17" />
                <Check v-else-if="task.status === 'completed'" :size="15" />
                <Circle v-else :size="19" :stroke-width="1.6" />
              </button>
              <div class="task-date"><strong>{{ formatDay(task.due_date) }}</strong><span>{{ formatWeekday(task.due_date) }}</span></div>
              <div class="task-content"><div class="task-title-line"><h3>{{ task.title }}</h3><span v-if="task.migrated" class="migrated-label">已迁移</span></div><p>{{ task.description }}</p></div>
              <div class="task-meta"><span><Clock3 :size="13" />{{ task.duration_minutes }} 分钟</span><span class="priority" :class="`priority-${task.priority}`">P{{ task.priority }}</span></div>
              <span class="task-index">{{ String(index + 1).padStart(2, '0') }}</span>
            </div>
          </div>

          <aside class="right-column">
            <section class="strategy-section">
              <div class="section-heading compact"><div><div class="eyebrow"><span class="eyebrow-line"></span>STUDY METHOD</div><h2>经验整合</h2></div><span class="round-icon"><Sparkles :size="16" /></span></div>
              <p class="strategy-copy">{{ plan.experience.strategy }}</p>
              <ul v-if="plan.experience.risks.length" class="risk-list"><li v-for="risk in plan.experience.risks" :key="risk">{{ risk }}</li></ul>
              <div v-if="plan.experience.context_used.length" class="context-used"><span>已纳入上下文</span><small v-for="item in plan.experience.context_used" :key="item">{{ item }}</small></div>
            </section>
            <section id="resources" class="resources-section">
              <div class="section-heading compact"><div><div class="eyebrow"><span class="eyebrow-line"></span>LEARNING MATERIALS</div><h2>资料书架</h2></div><Search :size="17" class="muted-icon" /></div>
              <a v-for="resource in plan.resources" :key="resource.title" class="resource-row" :href="resource.url || '#resources'" target="_blank" rel="noreferrer">
                <span class="resource-icon"><BookOpen :size="16" /></span><span class="resource-copy"><strong>{{ resource.title }}</strong><small>{{ resource.summary }}</small><i>{{ resource.source }}</i></span><ExternalLink :size="14" class="external-icon" />
              </a>
              <p v-if="!plan.resources.length" class="resource-empty">生成计划后，这里会出现匹配的学习资料。</p>
            </section>
          </aside>
        </section>

        <section v-if="plan.future_phases.length" class="future-section">
          <div class="section-heading">
            <div><div class="eyebrow"><span class="eyebrow-line"></span>THE ROAD AHEAD</div><h2>远期路线 <span class="coarse-label">保持弹性</span></h2></div>
            <span class="detail-tag"><CalendarDays :size="14" />阶段目标</span>
          </div>
          <div class="phase-grid">
            <article v-for="(phase, index) in plan.future_phases" :key="phase.starts_on" class="phase-item">
              <div class="phase-top"><span class="phase-number">{{ String(index + 3).padStart(2, '0') }}</span><span>{{ formatDate(phase.starts_on) }} — {{ formatDate(phase.ends_on) }}</span></div>
              <h3>{{ phase.title }}</h3><p>{{ phase.outcome }}</p>
            </article>
          </div>
        </section>
      </template>
      <footer class="page-footer"><span>知序 · 学习规划工作台</span><span>小步持续，进度自会显现。</span></footer>
    </main>
  </div>
</template>