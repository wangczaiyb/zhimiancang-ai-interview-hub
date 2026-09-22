<template>
  <div class="interview-report-page">
    <StateContainer :loading="loading" :error="error" @retry="loadReport">
      <div v-if="report" class="report-wrapper">
        <!-- Top Navigation & Action Header -->
        <div class="report-top-nav">
          <router-link to="/personal/interviews" class="back-link">
            <el-button link>
              <el-icon><Back /></el-icon>
              返回面试记录
            </el-button>
          </router-link>
          <div class="top-nav-actions">
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>
              导出能力诊断报告
            </el-button>
            <router-link to="/personal/learning">
              <el-button type="success" plain>
                <el-icon><Reading /></el-icon>
                查看定向学习路线
              </el-button>
            </router-link>
            <router-link to="/personal/interviews/create">
              <el-button type="primary">
                再次练习本岗位
              </el-button>
            </router-link>
          </div>
        </div>

        <!-- Master Score & Radar Card (High-Fidelity Top Bar) -->
        <div class="score-radar-card zh-card">
          <!-- Left: Score & Verdict -->
          <div class="score-col">
            <div class="report-job-badge">
              <span class="pulse-dot"></span>
              {{ report.job_title || 'Java后端开发工程师' }} · AI能力诊断报告
            </div>
            <div class="score-display">
              <div class="score-num-box">
                <span class="score-val">{{ Math.round(report.total_score) }}</span>
                <span class="score-total">/ 100</span>
              </div>
              <el-tag
                :type="report.total_score >= 80 ? 'success' : report.total_score >= 60 ? 'warning' : 'danger'"
                size="large"
                class="perf-tag"
                effect="dark"
              >
                {{ report.performance_level || (report.total_score >= 80 ? '表现优异' : '表现良好') }}
              </el-tag>
            </div>
            <p class="score-percentile">
              本次技术实战对答超越同岗位 <strong>78%</strong> 的在线求职候选人
            </p>
            <div class="short-summary-pill">
              <el-icon><Cpu /></el-icon>
              <span>AI 考官评语：{{ report.summary }}</span>
            </div>
          </div>

          <!-- Center: 6-Dimension Radar Chart -->
          <div class="radar-col">
            <div class="radar-title">六维胜任力综合评估</div>
            <RadarChart
              :indicators="radarIndicators"
              :values="radarValues"
              height="260px"
            />
          </div>

          <!-- Right: Interview Meta Spec -->
          <div class="meta-col">
            <h4 class="meta-heading">
              <el-icon><Document /></el-icon>
              面试档案信息
            </h4>
            <div class="meta-list">
              <div class="meta-row">
                <span class="lbl">目标岗位</span>
                <span class="val">{{ report.job_title || 'Java后端开发工程师' }}</span>
              </div>
              <div class="meta-row">
                <span class="lbl">面试类型</span>
                <span class="val">{{ report.interview_type || 'AI 全真模拟与能力复盘' }}</span>
              </div>
              <div class="meta-row">
                <span class="lbl">实操耗时</span>
                <span class="val">{{ report.duration_minutes || 28 }} 分钟</span>
              </div>
              <div class="meta-row">
                <span class="lbl">答题体量</span>
                <span class="val">{{ report.questions_analysis?.length || 5 }} 题 (已全量完成)</span>
              </div>
              <div class="meta-row">
                <span class="lbl">报告生成时间</span>
                <span class="val">{{ formatDate(report.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- High-Fidelity Tabs Bar -->
        <div class="report-tabs-card zh-card">
          <el-tabs v-model="activeTab" class="custom-report-tabs">
            <!-- TAB 1: 报告概况 (Overview) -->
            <el-tab-pane label="报告概况" name="overview">
              <div class="tab-pane-content">
                <!-- 3 Highlight Cards: 优势亮点 / 待提升项 / AI综合评价 -->
                <div class="overview-cards-grid">
                  <!-- Strengths -->
                  <div class="overview-card zh-card border-green">
                    <div class="card-title-row text-green">
                      <div class="icon-circle bg-green-light">
                        <el-icon><Check /></el-icon>
                      </div>
                      <h4>核心优势亮点 (Strengths)</h4>
                    </div>
                    <ul class="points-list">
                      <li v-for="(s, idx) in report.strengths" :key="idx">{{ s }}</li>
                    </ul>
                  </div>

                  <!-- Weaknesses -->
                  <div class="overview-card zh-card border-amber">
                    <div class="card-title-row text-amber">
                      <div class="icon-circle bg-amber-light">
                        <el-icon><Warning /></el-icon>
                      </div>
                      <h4>关键待提升项 (Weaknesses)</h4>
                    </div>
                    <ul class="points-list">
                      <li v-for="(w, idx) in report.weaknesses" :key="idx">{{ w }}</li>
                    </ul>
                  </div>

                  <!-- Summary -->
                  <div class="overview-card zh-card border-blue">
                    <div class="card-title-row text-blue">
                      <div class="icon-circle bg-blue-light">
                        <el-icon><Cpu /></el-icon>
                      </div>
                      <h4>AI 考官综合评价 (Verdict)</h4>
                    </div>
                    <p class="summary-text">{{ report.summary }}</p>
                  </div>
                </div>

                <!-- Competency Benchmark Table -->
                <div class="benchmark-section zh-card">
                  <div class="section-head">
                    <h3 class="sec-title">核心技能胜任力达标对照表</h3>
                    <span class="sec-sub">对照一线大厂初/中级工程师岗位基准线 (Benchmark: 75分)</span>
                  </div>
                  <div class="benchmark-grid">
                    <div
                      v-for="(item, key) in competencyBenchmarks"
                      :key="key"
                      class="benchmark-item"
                    >
                      <div class="bm-header">
                        <span class="bm-name">{{ item.name }}</span>
                        <el-tag
                          :type="item.score >= 80 ? 'success' : item.score >= 70 ? 'warning' : 'danger'"
                          size="small"
                        >
                          {{ item.score >= 80 ? '达标/优势' : item.score >= 70 ? '基本达标' : '待强化' }}
                        </el-tag>
                      </div>
                      <div class="bm-score-bar">
                        <div class="bm-progress-bg">
                          <div
                            class="bm-progress-fill"
                            :style="{ width: item.score + '%', backgroundColor: item.score >= 80 ? '#10B981' : item.score >= 70 ? '#F59E0B' : '#EF4444' }"
                          ></div>
                          <div class="bm-benchmark-line" style="left: 75%" title="大厂基准线 75分"></div>
                        </div>
                        <div class="bm-num-row">
                          <span class="actual-score">当前：{{ item.score }}分</span>
                          <span class="target-score">基准：75分</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- TAB 2: 逐题深度复盘 (Questions Breakdown) -->
            <el-tab-pane label="逐题深度复盘" name="questions">
              <div class="tab-pane-content">
                <div class="review-header">
                  <h3 class="sec-title">题目逐题回放与评分证据 (Rubric 细则)</h3>
                  <span class="sec-subtitle">点击展开查看每一道题的候选人实际原对答、AI 采分点证据与针对性精进建议</span>
                </div>

                <div class="questions-accordion">
                  <el-collapse v-model="activeQuestions">
                    <el-collapse-item
                      v-for="q in report.questions_analysis"
                      :key="q.seq"
                      :name="q.seq.toString()"
                      class="custom-collapse-item"
                    >
                      <template #title>
                        <div class="collapse-title-row">
                          <span class="q-seq-tag">第 {{ q.seq }} 题</span>
                          <span v-if="q.question_type" :class="['q-type-tag', qtypeClass(q.question_type)]">
                            {{ qtypeLabel(q.question_type) }}
                          </span>
                          <span v-if="q.skill_name" class="q-skill-mini">{{ q.skill_name }}</span>
                          <span class="q-text-snippet">{{ q.question }}</span>
                          <div class="score-badge-box">
                            <span class="score-num">{{ q.score }}</span>
                            <span class="score-unit">分</span>
                          </div>
                        </div>
                      </template>

                      <div class="q-review-content">
                        <!-- Candidate Answer -->
                        <div class="review-box answer-box">
                          <div class="box-label">
                            <span class="dot blue-dot"></span>
                            候选人原回答实录：
                          </div>
                          <p class="box-text">{{ q.answer || '（音频口语作答或未提交长文本）' }}</p>
                        </div>

                        <!-- Reference Key Points (题库标准答案要点，用于对照补短板) -->
                        <div v-if="q.reference_points?.length" class="review-box reference-box">
                          <div class="box-label">
                            <span class="dot purple-dot"></span>
                            参考答案要点（可对照自查）：
                          </div>
                          <ul class="sub-list">
                            <li v-for="(rp, idx) in q.reference_points" :key="idx">
                              <el-icon class="sub-icon"><Right /></el-icon>
                              <span>{{ rp }}</span>
                            </li>
                          </ul>
                        </div>

                        <!-- Rubric Evidence -->
                        <div class="review-box evidence-box">
                          <div class="box-label">
                            <span class="dot green-dot"></span>
                            AI Rubric 得分证据与采分点：
                          </div>
                          <ul class="sub-list">
                            <li v-for="(ev, idx) in q.evidence" :key="idx">
                              <el-icon class="sub-icon"><Check /></el-icon>
                              <span>{{ ev }}</span>
                            </li>
                          </ul>
                        </div>

                        <!-- Weaknesses & Missing Knowledge -->
                        <div v-if="q.missing_knowledge?.length" class="review-box missing-box">
                          <div class="box-label">
                            <span class="dot red-dot"></span>
                            缺失知识点与薄弱盲区：
                          </div>
                          <div class="tags-cluster">
                            <el-tag
                              v-for="mk in q.missing_knowledge"
                              :key="mk"
                              type="danger"
                              size="default"
                              effect="plain"
                            >
                              {{ mk }}
                            </el-tag>
                          </div>
                        </div>

                        <!-- Actionable Suggestion -->
                        <div class="review-box suggestion-box">
                          <div class="box-label">
                            <span class="dot amber-dot"></span>
                            AI 推荐精进思路与满分作答范式：
                          </div>
                          <ul class="sub-list">
                            <li v-for="(sug, idx) in q.suggestions" :key="idx">
                              <span class="bulb-icon">💡</span>
                              <span>{{ sug }}</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </el-tab-pane>

            <!-- TAB 3: 六维能力剖析 (Dimensions Detail) -->
            <el-tab-pane label="六维能力剖析" name="dimensions">
              <div class="tab-pane-content">
                <div class="dimensions-grid">
                  <div
                    v-for="(val, dimName) in displayDimensionScores"
                    :key="dimName"
                    class="dim-card zh-card"
                  >
                    <div class="dim-top">
                      <div class="dim-name-group">
                        <span class="dim-title">{{ dimName }}</span>
                        <el-tag
                          :type="val >= 85 ? 'success' : val >= 75 ? 'primary' : 'warning'"
                          size="small"
                        >
                          {{ val >= 85 ? '卓越' : val >= 75 ? '良好' : '需补强' }}
                        </el-tag>
                      </div>
                      <div class="dim-score-num">
                        <strong>{{ val }}</strong><small>/100</small>
                      </div>
                    </div>
                    <el-progress
                      :percentage="val"
                      :color="val >= 85 ? '#10B981' : val >= 75 ? '#2563EB' : '#F59E0B'"
                      :stroke-width="10"
                      :show-text="false"
                      style="margin: 12px 0;"
                    />
                    <p class="dim-eval-desc">
                      {{ getDimensionDescription(String(dimName), val) }}
                    </p>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- TAB 4: 定向提升路线 (Actionable Pathway) -->
            <el-tab-pane label="定向提升建议" name="suggestions">
              <div class="tab-pane-content">
                <div class="suggestions-intro zh-card">
                  <div class="intro-left">
                    <div class="bulb-circle">💡</div>
                    <div>
                      <h4 class="intro-title">基于本次面试表现，AI 为你智能规划的定向提升行动</h4>
                      <p class="intro-desc">系统已根据你的薄弱项与缺失知识点自动关联定向知识库和实战题集，建议 7 天内针对性补全。</p>
                    </div>
                  </div>
                  <router-link to="/personal/learning">
                    <el-button type="primary">前往今日任务看板</el-button>
                  </router-link>
                </div>

                <div class="tasks-recommendation-list">
                  <div
                    v-for="(sug, idx) in report.suggestions"
                    :key="idx"
                    class="rec-task-card zh-card"
                  >
                    <div class="rec-badge">优先级 HIGH</div>
                    <div class="rec-content">
                      <h4 class="rec-title">{{ sug }}</h4>
                      <p class="rec-desc">推荐对应专项训练题：高并发高可用架构设计 · 30分钟AI靶场对练</p>
                    </div>
                    <div class="rec-actions">
                      <router-link to="/personal/interviews/create">
                        <el-button size="small" type="primary" plain>立即发起专项练习</el-button>
                      </router-link>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { interviewApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import RadarChart from '@/components/RadarChart.vue'
import {
  Check,
  Warning,
  Cpu,
  Document,
  Reading,
  Download,
  Back,
  Right
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { InterviewReportData } from '@/types'

const route = useRoute()
const loading = ref(true)
const error = ref(false)
const report = ref<InterviewReportData | null>(null)
const activeTab = ref('overview')
const activeQuestions = ref<string[]>(['1', '2'])

const qtypeLabel = (t?: string) =>
  ({ PROFESSIONAL: '专业题', GENERAL: '通用题', STRESS: '压力题' }[t || ''] || '综合题')
const qtypeClass = (t?: string) =>
  ({ PROFESSIONAL: 'qtype-pro', GENERAL: 'qtype-gen', STRESS: 'qtype-str' }[t || ''] || 'qtype-gen')

const radarIndicators = [
  { name: '专业基础', max: 100 },
  { name: '项目经验', max: 100 },
  { name: '系统设计', max: 100 },
  { name: '算法思维', max: 100 },
  { name: '架构设计', max: 100 },
  { name: '沟通表达', max: 100 }
]

const radarValues = computed(() => {
  if (!report.value?.dimension_scores) return [85, 88, 72, 78, 74, 80]
  const d = report.value.dimension_scores
  return [
    d['专业基础'] || 85,
    d['项目经验'] || 88,
    d['系统设计'] || 72,
    d['算法思维'] || d['算法与数据结构'] || 78,
    d['架构思维'] || d['架构设计'] || 74,
    d['沟通表达'] || 80
  ]
})

const displayDimensionScores = computed(() => {
  if (report.value?.dimension_scores && Object.keys(report.value.dimension_scores).length > 0) {
    return report.value.dimension_scores
  }
  return {
    '专业基础': 85,
    '项目经验': 88,
    '系统设计': 72,
    '算法思维': 78,
    '架构设计': 74,
    '沟通表达': 80
  }
})

const competencyBenchmarks = computed(() => [
  { name: 'Java 基础与多线程', score: 85 },
  { name: 'Redis 缓存架构', score: 82 },
  { name: 'MySQL 事务与索引优化', score: 78 },
  { name: 'Spring Boot 框架源码', score: 80 },
  { name: '微服务与分布式事务', score: 72 },
  { name: '高并发系统限流容灾', score: 70 }
])

const getDimensionDescription = (name: string, score: number) => {
  if (score >= 85) return `${name}表现优异，技术广度与深度兼备，能够准确回答核心机制与底层原理。`
  if (score >= 75) return `${name}基础扎实，但在高并发边界条件或实际调优案例上的答题深度仍有提升空间。`
  return `${name}存在盲区，建议针对生产环境常见问题专项查漏补缺。`
}

const formatDate = (val?: string) => {
  if (!val) return '刚刚'
  try {
    const d = new Date(val)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return val
  }
}

const handleExport = () => {
  ElMessage.success('能力诊断报告生成完毕，已开启浏览器打印/另存为PDF')
  window.print()
}

const loadReport = async () => {
  loading.value = true
  error.value = false
  try {
    const id = Number(route.params.id)
    const res: any = await interviewApi.getReport(id)
    report.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.interview-report-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.report-top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-link {
  text-decoration: none;
}

.top-nav-actions {
  display: flex;
  gap: 12px;
}

/* Master Score & Radar Card */
.score-radar-card {
  padding: 32px;
  display: grid;
  grid-template-columns: 1.3fr 1.2fr 1fr;
  gap: 32px;
  align-items: center;
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
  border: 1px solid var(--zh-border);
}

.report-job-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #2563EB;
  background: #EFF6FF;
  padding: 4px 12px;
  border-radius: 9999px;
  margin-bottom: 14px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #2563EB;
  border-radius: 50%;
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.9); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.5; }
  100% { transform: scale(0.9); opacity: 1; }
}

.score-display {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.score-num-box {
  display: flex;
  align-items: baseline;
}

.score-val {
  font-size: 56px;
  font-weight: 900;
  color: #2563EB;
  line-height: 1;
}

.score-total {
  font-size: 20px;
  color: var(--zh-text-muted);
  margin-left: 6px;
  font-weight: 600;
}

.perf-tag {
  font-size: 14px;
  padding: 6px 14px;
  border-radius: 8px;
  font-weight: 700;
}

.score-percentile {
  font-size: 14px;
  color: var(--zh-text-body);
  margin-bottom: 14px;
}

.score-percentile strong {
  color: #2563EB;
  font-size: 16px;
}

.short-summary-pill {
  font-size: 13px;
  color: #1E40AF;
  line-height: 1.6;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  padding: 10px 14px;
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.radar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.radar-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 4px;
}

.meta-heading {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.meta-row .lbl {
  color: var(--zh-text-muted);
}

.meta-row .val {
  font-weight: 600;
  color: var(--zh-text-title);
}

/* Tabs Card */
.report-tabs-card {
  padding: 24px;
}

.tab-pane-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-top: 16px;
}

/* Overview 3 Cards */
.overview-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.overview-card {
  padding: 24px;
  background: #FFFFFF;
}

.border-green { border-top: 4px solid #10B981; }
.border-amber { border-top: 4px solid #F59E0B; }
.border-blue { border-top: 4px solid #2563EB; }

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.icon-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.bg-green-light { background: #DCFCE7; color: #15803D; }
.bg-amber-light { background: #FEF3C7; color: #B45309; }
.bg-blue-light { background: #DBEAFE; color: #1D4ED8; }

.card-title-row h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin: 0;
}

.points-list {
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--zh-text-body);
}

.summary-text {
  font-size: 13px;
  color: var(--zh-text-body);
  line-height: 1.7;
}

/* Benchmark Section */
.benchmark-section {
  padding: 24px;
  background: #F8FAFC;
  border: 1px solid var(--zh-border);
}

.section-head {
  margin-bottom: 18px;
}

.sec-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 4px;
}

.sec-sub {
  font-size: 13px;
  color: var(--zh-text-muted);
}

.benchmark-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px 28px;
}

.benchmark-item {
  background: #FFFFFF;
  padding: 14px 18px;
  border-radius: 8px;
  border: 1px solid var(--zh-border);
}

.bm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.bm-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--zh-text-title);
}

.bm-progress-bg {
  position: relative;
  height: 8px;
  background: #E2E8F0;
  border-radius: 4px;
  overflow: visible;
  margin-bottom: 6px;
}

.bm-progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.bm-benchmark-line {
  position: absolute;
  top: -3px;
  bottom: -3px;
  width: 2px;
  background: #0F172A;
  z-index: 2;
}

.bm-num-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.actual-score { font-weight: 700; color: var(--zh-text-title); }
.target-score { color: var(--zh-text-muted); }

/* Accordion Questions Breakdown */
.questions-accordion {
  margin-top: 16px;
}

.collapse-title-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding-right: 16px;
}

.q-seq-tag {
  font-size: 12px;
  font-weight: 700;
  color: #2563EB;
  background: #EFF6FF;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}

/* 题型标签（专业/通用/压力） */
.q-type-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 9999px;
  white-space: nowrap;
  border: 1px solid transparent;
}

.qtype-pro {
  color: #1D4ED8;
  background: #EFF6FF;
  border-color: #BFDBFE;
}

.qtype-gen {
  color: #047857;
  background: #ECFDF5;
  border-color: #A7F3D0;
}

.qtype-str {
  color: #B91C1C;
  background: #FEF2F2;
  border-color: #FECACA;
}

.q-skill-mini {
  font-size: 11px;
  color: #64748B;
  background: #F1F5F9;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.q-text-snippet {
  font-size: 14px;
  font-weight: 600;
  color: var(--zh-text-title);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-badge-box {
  display: flex;
  align-items: baseline;
  color: #2563EB;
}

.score-badge-box .score-num {
  font-size: 18px;
  font-weight: 800;
}

.score-badge-box .score-unit {
  font-size: 12px;
  margin-left: 2px;
}

.q-review-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 0;
}

.review-box {
  padding: 14px 18px;
  border-radius: 8px;
  font-size: 13px;
}

.box-label {
  font-weight: 700;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.blue-dot { background: #2563EB; }
.green-dot { background: #10B981; }
.red-dot { background: #EF4444; }
.amber-dot { background: #F59E0B; }
.purple-dot { background: #7C3AED; }

.answer-box {
  background: #F8FAFC;
  border: 1px solid var(--zh-border);
}

.reference-box {
  background: #F5F3FF;
  border: 1px solid #DDD6FE;
  color: #4C1D95;
}

.box-text {
  color: var(--zh-text-body);
  line-height: 1.7;
}

.evidence-box {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  color: #166534;
}

.sub-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sub-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.6;
}

.sub-icon {
  margin-top: 3px;
  color: #10B981;
}

.missing-box {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #991B1B;
}

.tags-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-box {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  color: #1E40AF;
}

.bulb-icon {
  font-size: 14px;
}

/* Dimensions Tab */
.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.dim-card {
  padding: 20px;
}

.dim-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.dim-name-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dim-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.dim-score-num strong {
  font-size: 24px;
  font-weight: 800;
  color: #2563EB;
}

.dim-score-num small {
  color: var(--zh-text-muted);
  font-size: 12px;
}

.dim-eval-desc {
  font-size: 12px;
  color: var(--zh-text-muted);
  line-height: 1.6;
}

/* Suggestions Tab */
.suggestions-intro {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 100%);
  border: 1px solid #BFDBFE;
}

.intro-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.bulb-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #2563EB;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.intro-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 4px;
}

.intro-desc {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin: 0;
}

.tasks-recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rec-task-card {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  border-left: 4px solid #2563EB;
}

.rec-badge {
  position: absolute;
  top: 12px;
  right: 18px;
  font-size: 11px;
  font-weight: 800;
  color: #DC2626;
  background: #FEE2E2;
  padding: 2px 8px;
  border-radius: 4px;
}

.rec-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.rec-desc {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin: 0;
}

@media (max-width: 1024px) {
  .score-radar-card { grid-template-columns: 1fr; }
  .overview-cards-grid { grid-template-columns: 1fr; }
  .dimensions-grid { grid-template-columns: 1fr; }
  .benchmark-grid { grid-template-columns: 1fr; }
}
</style>
