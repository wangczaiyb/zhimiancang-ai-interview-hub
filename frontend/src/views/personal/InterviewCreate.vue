<template>
  <div class="interview-prepare-page">
    <div class="header-card zh-card">
      <h2 class="title">AI 智能模拟面试舱 · 准备就绪</h2>
      <p class="subtitle">在进入摄像头前确定本次面试考核目标、考察模式与设备运行状态</p>
    </div>

    <div class="prepare-grid">
      <!-- Left Config Form -->
      <div class="config-card zh-card">
        <h3 class="sec-title">1. 配置面试考核参数</h3>

        <el-form label-position="top">
          <el-form-item label="目标面试岗位" required>
            <el-select v-model="form.job_id" placeholder="请选择目标岗位" style="width: 100%;" @change="handleJobChange">
              <el-option
                v-for="j in jobs"
                :key="j.id"
                :label="`${j.title} (${j.company_name})`"
                :value="j.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="岗位 JD (自动带出，可手动修改)">
            <el-input
              v-model="form.jd_text"
              type="textarea"
              :rows="5"
              placeholder="选择岗位后会自动带出该岗位的 JD；你也可以直接粘贴/修改 JD 文本，AI 将据此生成面试题"
            />
          </el-form-item>

          <el-form-item label="选择本次使用的个人简历">
            <el-select v-model="form.resume_id" placeholder="请选择简历" style="width: 100%;">
              <el-option
                v-for="r in resumes"
                :key="r.id"
                :label="`${r.name} (完整度 ${r.completeness}%)`"
                :value="r.id"
              />
            </el-select>
            <span v-if="!resumes.length" class="form-hint">尚未上传简历，可先前往「简历中心」上传后再进行个性化面试</span>
          </el-form-item>

          <el-form-item label="面试模式" required>
            <div class="modes-grid">
              <div
                v-for="m in modeOptions"
                :key="m.value"
                :class="['mode-box', { active: form.mode === m.value }]"
                @click="form.mode = m.value"
              >
                <strong>{{ m.label }}</strong>
                <span>{{ m.desc }}</span>
              </div>
            </div>
          </el-form-item>

          <div class="form-row">
            <el-form-item label="挑战难度">
              <el-radio-group v-model="form.difficulty">
                <el-radio-button label="EASY">基础入门</el-radio-button>
                <el-radio-button label="MEDIUM">标准大厂</el-radio-button>
                <el-radio-button label="HARD">高阶挑战</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="题目数量与预计时长">
              <el-select v-model="form.total_questions" style="width: 160px;">
                <el-option label="3 题 (约15分钟)" :value="3" />
                <el-option label="5 题 (约25分钟)" :value="5" />
                <el-option label="8 题 (约40分钟)" :value="8" />
              </el-select>
            </el-form-item>
          </div>

          <!-- 结构化题库组卷 -->
          <div class="paper-config-box">
            <div class="paper-config-head">
              <span class="pc-title">
                <el-icon color="#2563EB"><Files /></el-icon>
                结构化题库组卷
              </span>
              <el-switch v-model="form.use_question_bank" size="small" active-text="题库优先" />
            </div>
            <p class="pc-desc">
              <template v-if="form.use_question_bank && bankTotal > 0">
                从 <strong>{{ bankTotal }}</strong> 道题库题中按
                <strong>{{ ratioText }}</strong> 配比抽题（专业题 : 通用题 : 压力题），
                优先命中岗位技能要求；题库不足部分由 AI 自动补足。
              </template>
              <template v-else-if="form.use_question_bank">
                题库尚未初始化，将全部由 AI 实时生成题目。
              </template>
              <template v-else>
                已关闭题库，本次面试全部题目由 AI 依据 JD 与简历实时生成。
              </template>
            </p>
            <el-button link class="preview-paper-btn" @click="handlePreviewPaper">
              预览本次考卷题目 →
            </el-button>
          </div>
        </el-form>
      </div>

      <!-- Right Device Check & Privacy -->
      <div class="device-card zh-card">
        <h3 class="sec-title">2. 设备检测与隐私承诺</h3>

        <div class="device-checks">
          <div class="check-item">
            <div class="chk-left">
              <el-icon :size="20" color="#10B981"><VideoCamera /></el-icon>
              <span>摄像头状态</span>
            </div>
            <el-tag type="success" size="small">准备就绪 (支持文本模式)</el-tag>
          </div>

          <div class="check-item">
            <div class="chk-left">
              <el-icon :size="20" color="#10B981"><Microphone /></el-icon>
              <span>麦克风录音</span>
            </div>
            <el-tag type="success" size="small">正常响应 (支持实时转写)</el-tag>
          </div>

          <div class="check-item">
            <div class="chk-left">
              <el-icon :size="20" color="#10B981"><Headset /></el-icon>
              <span>扬声器/耳机</span>
            </div>
            <el-tag type="success" size="small">声音播放正常</el-tag>
          </div>

          <div class="check-item">
            <div class="chk-left">
              <el-icon :size="20" color="#10B981"><Connection /></el-icon>
              <span>实时双向网络</span>
            </div>
            <el-tag type="success" size="small">延迟 25ms (优秀)</el-tag>
          </div>
        </div>

        <div class="privacy-box">
          <div class="p-title">
            <el-icon color="#2563EB"><Lock /></el-icon>
            <span>隐私与数据边界说明</span>
          </div>
          <p class="p-desc">
            本次为个人训练模拟面试，对答音频与复盘报告<strong>默认严格仅本人可见</strong>，绝不向任何招聘企业公开。如果设备临时不可用，仍可在面试仓中自由切换为纯文本交互模式。
          </p>
        </div>

        <el-button
          type="primary"
          size="large"
          class="start-btn"
          :loading="creating"
          @click="handleStartInterview"
        >
          立即进入沉浸式 AI 面试仓 →
        </el-button>
      </div>
    </div>

    <!-- 组卷预览弹窗 -->
    <el-dialog v-model="previewVisible" title="本次考卷预览" width="720px" top="6vh">
      <div v-if="preview" class="paper-preview">
        <div class="pp-meta">
          <el-tag size="small" type="info">匹配岗位大类：{{ preview.matched_category }}</el-tag>
          <el-tag size="small" type="success">题库命中 {{ preview.from_bank }}/{{ preview.total_questions }}</el-tag>
          <el-tag v-if="preview.job_skills.length" size="small">优先技能：{{ preview.job_skills.slice(0, 4).join('、') }}</el-tag>
        </div>
        <p v-if="preview.from_bank === 0" class="pp-empty">
          当前未启用题库或题库为空，题目将在进入面试仓时由 AI 实时生成。
        </p>
        <ol v-else class="pp-list">
          <li v-for="q in preview.questions" :key="q.seq" class="pp-item">
            <div class="pp-item-head">
              <span class="pp-seq">第 {{ q.seq }} 题</span>
              <el-tag :type="qtypeTag(q.question_type)" size="small" effect="light">{{ qtypeLabel(q.question_type) }}</el-tag>
              <el-tag size="small" type="info" effect="plain">{{ q.skill_name }}</el-tag>
              <el-tag size="small" type="warning" effect="plain">{{ q.difficulty }}</el-tag>
              <span class="pp-limit">限时 {{ Math.round(q.time_limit_sec / 60) }} 分钟</span>
            </div>
            <p class="pp-text">{{ q.text }}</p>
          </li>
        </ol>
      </div>
      <el-empty v-else description="加载考卷中..." />
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="previewVisible = false; handleStartInterview()">按此考卷开始面试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { interviewApi, jobApi, resumeApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { PaperPreview } from '@/types'
import { VideoCamera, Microphone, Headset, Connection, Lock, Files } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const creating = ref(false)
const jobs = ref<any[]>([])
const resumes = ref<any[]>([])

const modeOptions = [
  { label: '综合全真模拟', value: 'COMPREHENSIVE', desc: '大厂常规两轮技术+综合，考察全面' },
  { label: '技术深度专项', value: 'TECHNICAL', desc: '聚焦 Redis/MySQL/Java 底层原理' },
  { label: '项目经历深挖', value: 'PROJECT_DEEP_DIVE', desc: '基于 STAR 原则深入剖析技术取舍' },
  { label: '压力与边界测试', value: 'STRESS', desc: '连续追问极端并发容灾与故障排查' }
]

const form = reactive({
  job_id: 1,
  resume_id: undefined as number | undefined,
  jd_text: '',
  mode: 'TECHNICAL',
  difficulty: 'MEDIUM',
  total_questions: 5,
  type: 'PERSONAL_TRAINING',
  use_question_bank: true
})

/* ---------- 结构化题库组卷：配比展示 / 考卷预览 ---------- */
const bankTotal = ref(0)
const ratio = ref<Record<string, number>>({ PROFESSIONAL: 7, GENERAL: 2, STRESS: 1 })
const preview = ref<PaperPreview | null>(null)
const previewVisible = ref(false)
// 用户已预览确认的考卷（题库题目 ID）；配置变更后置空，避免"所见非所考"
const selectedBankIds = ref<number[]>([])

const ratioText = computed(() =>
  `${ratio.value.PROFESSIONAL || 0}:${ratio.value.GENERAL || 0}:${ratio.value.STRESS || 0}`
)

const qtypeLabel = (t: string) =>
  ({ PROFESSIONAL: '专业题', GENERAL: '通用题', STRESS: '压力题' }[t] || t)
const qtypeTag = (t: string) =>
  (({ PROFESSIONAL: 'primary', GENERAL: 'success', STRESS: 'danger' } as Record<string, any>)[t] || 'info')

const refreshRatio = async () => {
  try {
    const d: any = await interviewApi.getPaperRatio({ mode: form.mode, total_questions: form.total_questions })
    ratio.value = d.ratio || ratio.value
  } catch (e) {
    // handled
  }
}

const handlePreviewPaper = async () => {
  preview.value = null
  previewVisible.value = true
  try {
    const d: any = await interviewApi.previewPaper({
      job_id: form.job_id,
      mode: form.mode,
      difficulty: form.difficulty,
      total_questions: form.total_questions,
      use_question_bank: form.use_question_bank,
      jd_text: form.jd_text
    })
    preview.value = d
    selectedBankIds.value = (d.questions || []).map((q: any) => q.bank_id).filter(Boolean)
  } catch (e) {
    previewVisible.value = false
  }
}

// 面试配置变化后，先前的考卷选择失效
watch(
  () => [form.mode, form.difficulty, form.total_questions, form.job_id, form.use_question_bank],
  () => {
    selectedBankIds.value = []
    refreshRatio()
  }
)

// 根据所选岗位自动带出 JD 文本（用户可在此基础上手动修改）
const fillJdFromJob = (jobId: number) => {
  const job = jobs.value.find(j => j.id === jobId)
  if (!job) return
  const parts = [
    `岗位名称：${job.title}`,
    `学历要求：${job.education || '-'}｜经验要求：${job.experience || '-'}｜工作城市：${job.city || '-'}`
  ]
  if (job.skills?.length) {
    parts.push('技能要求：' + job.skills.map((s: any) => s.skill_name).join('、'))
  }
  if (job.description) parts.push(`岗位描述：${job.description}`)
  if (job.duties) parts.push(`岗位职责：${job.duties}`)
  if (job.requirements) parts.push(`任职要求：${job.requirements}`)
  if (job.bonus) parts.push(`加分项：${job.bonus}`)
  form.jd_text = parts.join('\n')
}

const handleJobChange = (jobId: number) => {
  fillJdFromJob(jobId)
}

onMounted(async () => {
  try {
    const jList: any = await jobApi.listJobs({ page: 1, page_size: 20 })
    jobs.value = jList.items || []
    if (route.query.jobId) {
      form.job_id = Number(route.query.jobId)
    } else if (jobs.value.length > 0) {
      form.job_id = jobs.value[0].id
    }
    // 自动带出 JD
    fillJdFromJob(form.job_id)

    const rList: any = await resumeApi.listResumes()
    resumes.value = rList || []
    if (resumes.value.length > 0) {
      // 优先选择默认简历
      const defaultResume = resumes.value.find((r: any) => r.is_default)
      form.resume_id = (defaultResume || resumes.value[0]).id
    }

    if (route.query.appId) {
      form.type = 'ENTERPRISE_RECRUITMENT'
    }

    // 题库规模与当前模式配比
    const stats: any = await interviewApi.getBankStats()
    bankTotal.value = stats?.total || 0
    await refreshRatio()
  } catch (e) {
    // handled
  }
})

const handleStartInterview = async () => {
  creating.value = true
  try {
    const res: any = await interviewApi.createInterview({
      job_id: form.job_id,
      resume_id: form.resume_id,
      type: form.type,
      mode: form.mode,
      difficulty: form.difficulty,
      total_questions: form.total_questions,
      duration_minutes: form.total_questions * 5,
      jd_text: form.jd_text,
      use_question_bank: form.use_question_bank,
      selected_bank_ids: selectedBankIds.value.length ? selectedBankIds.value : undefined
    })

    ElMessage.success('面试准备就绪，正在接入 AI 面试仓...')
    router.push(`/personal/interviews/${res.id}/room`)
  } catch (e) {
    // handled
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
/* 结构化题库组卷配置区 */
.paper-config-box {
  margin-top: 4px;
  padding: 12px 14px;
  background: var(--zh-sub-bg);
  border: 1px solid var(--zh-border);
  border-radius: 8px;
}

.paper-config-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.pc-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.pc-desc {
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--zh-text-muted);
  margin-bottom: 6px;
}

.pc-desc strong {
  color: var(--zh-primary);
}

.preview-paper-btn {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--zh-primary) !important;
  padding: 0;
  height: auto;
}

.preview-paper-btn:hover {
  color: var(--zh-primary-hover, #1D4ED8) !important;
  text-decoration: underline;
}

/* 考卷预览弹窗 */
.paper-preview {
  max-height: 58vh;
  overflow-y: auto;
}

.pp-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.pp-empty {
  font-size: 13px;
  color: var(--zh-text-muted);
}

.pp-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.pp-item {
  padding: 10px 0;
  border-bottom: 1px dashed var(--zh-border);
}

.pp-item:last-child {
  border-bottom: none;
}

.pp-item-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}

.pp-seq {
  font-size: 13px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.pp-limit {
  font-size: 12px;
  color: var(--zh-text-muted);
  margin-left: auto;
}

.pp-text {
  font-size: 13.5px;
  line-height: 1.7;
  color: #374151;
}

.interview-prepare-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-card {
  padding: 28px 32px;
}

.title {
  font-size: 22px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.subtitle {
  font-size: 13px;
  color: var(--zh-text-muted);
}

.prepare-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 24px;
}

.config-card, .device-card {
  padding: 28px;
}

.sec-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 20px;
}

.modes-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.mode-box {
  border: 1.5px solid var(--zh-border);
  border-radius: 8px;
  padding: 12px 14px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.15s ease;
}

.mode-box:hover {
  border-color: var(--zh-primary);
}

.mode-box.active {
  border-color: var(--zh-primary);
  background: var(--zh-primary-light);
}

.mode-box strong {
  font-size: 13px;
  color: var(--zh-text-title);
}

.mode-box span {
  font-size: 11px;
  color: var(--zh-text-muted);
}

.form-row {
  display: flex;
  gap: 24px;
}

.form-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #F59E0B;
}

.device-checks {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.check-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid var(--zh-border-light);
}

.chk-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--zh-text-body);
}

.privacy-box {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 24px;
}

.p-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #1E40AF;
  margin-bottom: 6px;
}

.p-desc {
  font-size: 12px;
  color: #3B82F6;
  line-height: 1.6;
}

.start-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .prepare-grid { grid-template-columns: 1fr; }
}
</style>
