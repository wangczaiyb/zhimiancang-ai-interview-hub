<template>
  <div class="learning-roadmap-page">
    <div class="header-box zh-card">
      <div class="header-content">
        <div>
          <h2 class="title">AI 定向学习与技能攻坚路线</h2>
          <p class="subtitle">针对求职目标【{{ plan?.target_job_title || 'Java后端开发工程师' }}】与岗位 JD 自动生成，分阶段推进</p>
        </div>
        <el-button type="primary" plain :loading="regenerating" @click="openRegenerate">
          重新生成学习规划 ⟳
        </el-button>
      </div>
    </div>

    <StateContainer :loading="loading" :error="error" @retry="loadPlan">
      <div v-if="plan" class="roadmap-container">
        <div
          v-for="(stage, sIdx) in stages"
          :key="stage.stage"
          class="stage-block"
        >
          <!-- 阶段标题 -->
          <div class="stage-head">
            <div class="stage-title-row">
              <span class="stage-index">阶段 {{ Number(sIdx) + 1 }}</span>
              <h3 class="stage-name">{{ stage.stage }}</h3>
            </div>
            <span class="stage-progress">{{ stage.completed }} / {{ stage.total }} 已完成</span>
          </div>

          <!-- 阶段内待办 -->
          <div class="tasks-list">
            <div
              v-for="task in stage.tasks"
              :key="task.id"
              :class="['task-card zh-card', { completed: task.status === 'COMPLETED' }]"
            >
              <div class="task-head">
                <div class="task-badge-row">
                  <el-tag size="small" :type="task.priority === 'HIGH' ? 'danger' : 'warning'">
                    {{ task.priority === 'HIGH' ? '高频痛点' : '进阶提升' }}
                  </el-tag>
                  <el-tag size="small" type="info">{{ task.competency_name }}</el-tag>
                </div>

                <span v-if="task.status === 'COMPLETED'" class="status-tag text-green">✓ 已掌握完成</span>
                <span v-else class="status-tag text-amber">待攻克</span>
              </div>

              <h4 class="task-title">{{ task.title }}</h4>
              <p class="task-reason">制定依据：{{ task.reason }}</p>

              <div class="task-foot">
                <div class="progress-box">
                  <span class="prog-lbl">攻坚进度</span>
                  <el-progress :percentage="task.progress" :stroke-width="6" style="width: 140px;" />
                </div>

                <div class="task-actions">
                  <router-link to="/personal/interviews/create">
                    <el-button size="small" type="primary" plain>进入定向模拟练习</el-button>
                  </router-link>
                  <el-button
                    v-if="task.status !== 'COMPLETED'"
                    size="small"
                    type="success"
                    @click="completeTask(task.id)"
                  >
                    标记已学完
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </StateContainer>

    <!-- 依据 JD 重新生成学习路线 -->
    <el-dialog v-model="regenerateVisible" title="依据岗位 JD 生成学习路线" width="640px">
      <p class="dialog-tip">
        可粘贴目标岗位 JD，AI 将据此生成分阶段学习待办；留空则默认使用「个人档案」中的目标岗位。
      </p>
      <el-input
        v-model="jdInput"
        type="textarea"
        :rows="8"
        placeholder="粘贴岗位 JD 文本（可选）..."
      />
      <template #footer>
        <el-button @click="regenerateVisible = false">取消</el-button>
        <el-button type="primary" :loading="regenerating" @click="handleRegenerate">
          生成学习路线
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { personalApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import { ElMessage } from 'element-plus'

const loading = ref(true)
const error = ref(false)
const regenerating = ref(false)
const plan = ref<any>(null)

const regenerateVisible = ref(false)
const jdInput = ref('')

// 优先使用后端返回的分阶段聚合；无 stages 时按任务 stage 字段本地聚合
const stages = computed(() => {
  const data = plan.value
  if (!data) return []
  if (Array.isArray(data.stages) && data.stages.length) {
    return data.stages
  }
  const map: Record<string, any[]> = {}
  for (const t of data.tasks || []) {
    const key = t.stage || '第一阶段 · 基础夯实'
    if (!map[key]) map[key] = []
    map[key].push(t)
  }
  return Object.entries(map).map(([stage, tasks]) => ({
    stage,
    tasks,
    total: tasks.length,
    completed: tasks.filter(x => x.status === 'COMPLETED').length
  }))
})

const loadPlan = async () => {
  loading.value = true
  error.value = false
  try {
    const res: any = await personalApi.getLearningPlan()
    plan.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

const openRegenerate = () => {
  regenerateVisible.value = true
}

const handleRegenerate = async () => {
  regenerating.value = true
  try {
    await personalApi.regenerateLearningPlan({ jd_text: jdInput.value || undefined })
    ElMessage.success('学习路线已按岗位 JD 重新生成！')
    regenerateVisible.value = false
    loadPlan()
  } catch (e) {
    // handled
  } finally {
    regenerating.value = false
  }
}

const completeTask = async (taskId: number) => {
  try {
    await personalApi.completeTask(taskId)
    ElMessage.success('任务已标记为完成，能力分已同步提升！')
    loadPlan()
  } catch (e) {
    // handled
  }
}

onMounted(() => {
  loadPlan()
})
</script>

<style scoped>
.learning-roadmap-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-box {
  padding: 24px 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.roadmap-container {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.stage-block {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stage-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-left: 4px;
}

.stage-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stage-index {
  font-size: 12px;
  font-weight: 700;
  color: #2563EB;
  background: #EFF6FF;
  padding: 3px 10px;
  border-radius: 6px;
}

.stage-name {
  font-size: 17px;
  font-weight: 800;
  color: var(--zh-text-title);
}

.stage-progress {
  font-size: 12px;
  color: var(--zh-text-muted);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  padding: 24px;
  transition: all 0.15s ease;
}

.task-card.completed {
  background: #F8FAFC;
  opacity: 0.85;
}

.task-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  font-size: 13px;
  font-weight: 600;
}
.text-green { color: #10B981; }
.text-amber { color: #D97706; }

.task-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}

.task-reason {
  font-size: 13px;
  color: var(--zh-text-muted);
  line-height: 1.6;
  margin-bottom: 20px;
}

.task-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--zh-border-light);
  padding-top: 16px;
}

.progress-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prog-lbl {
  font-size: 12px;
  color: var(--zh-text-muted);
}

.task-actions {
  display: flex;
  gap: 12px;
}

.dialog-tip {
  font-size: 13px;
  color: var(--zh-text-muted);
  line-height: 1.6;
  margin-bottom: 12px;
}
</style>
