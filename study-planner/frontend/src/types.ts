export type TaskStatus = 'todo' | 'in_progress' | 'completed'

export interface PlanRequest {
  learner_id: string
  goal: string
  subject: string
  current_level: string
  weekly_hours: number
  study_days_per_week: number
  session_minutes: number
  deadline: string
  context_notes: string
}

export interface GoalAnalysis {
  clarified_goal: string
  assumptions: string[]
  milestones: string[]
  estimated_weeks: number
}

export interface StudyResource {
  title: string
  url?: string | null
  summary: string
  source: string
}

export interface ExperienceBrief {
  strategy: string
  risks: string[]
  context_used: string[]
}

export interface StudyTask {
  id: string
  title: string
  description: string
  due_date: string
  duration_minutes: number
  priority: number
  status: TaskStatus
  migrated: boolean
  migrated_from?: string | null
}

export interface StudyPhase {
  title: string
  starts_on: string
  ends_on: string
  focus: string
  outcome: string
}

export interface AgentTrace {
  name: string
  status: string
  detail: string
}

export interface StudyPlan {
  plan_id: string
  learner_id: string
  goal: GoalAnalysis
  experience: ExperienceBrief
  resources: StudyResource[]
  near_term_tasks: StudyTask[]
  future_phases: StudyPhase[]
  migrated_tasks_count: number
  agents: AgentTrace[]
  generated_at: string
}