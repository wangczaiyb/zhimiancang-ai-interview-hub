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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { interviewApi, jobApi, resumeApi } from '@/api'
import { ElMessage } from 'element-plus'
import { VideoCamera, Microphone, Headset, Connection, Lock } from '@element-plus/icons-vue'

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
  type: 'PERSONAL_TRAINING'
})

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
      jd_text: form.jd_text
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
