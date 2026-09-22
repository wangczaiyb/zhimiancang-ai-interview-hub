<template>
  <div class="interviews-list-page">
    <div class="header-box zh-card">
      <div class="header-content">
        <div>
          <h2 class="title">模拟面试记录与复盘中心</h2>
          <p class="subtitle">沉淀历史面试对答数据，点击报告可查看五维能力雷达与证据式复盘</p>
        </div>
        <router-link to="/personal/interviews/create">
          <el-button type="primary">发起新面试训练 +</el-button>
        </router-link>
      </div>
    </div>

    <StateContainer :loading="loading" :empty="!loading && interviews.length === 0" empty-text="暂无面试记录" empty-action-text="立即开始模拟面试" @empty-action="$router.push('/personal/interviews/create')">
      <div class="interviews-table-card zh-card">
        <el-table :data="interviews" stripe style="width: 100%;">
          <el-table-column prop="job_title" label="面试目标岗位" min-width="180">
            <template #default="{ row }">
              <strong style="color: var(--zh-text-title);">{{ row.job_title }}</strong>
            </template>
          </el-table-column>

          <el-table-column prop="type" label="性质" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.type === 'ENTERPRISE_RECRUITMENT'" type="warning" size="small">企业招聘面</el-tag>
              <el-tag v-else type="primary" size="small">个人训练面</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="mode" label="考察模式" width="130">
            <template #default="{ row }">
              {{ getModeText(row.mode) }}
            </template>
          </el-table-column>

          <el-table-column prop="score" label="综合得分" width="120">
            <template #default="{ row }">
              <span v-if="row.score" style="font-size: 16px; font-weight: 800; color: #2563EB;">
                {{ row.score }} 分
              </span>
              <span v-else style="color: #94A3B8;">未生成</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="面试状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'COMPLETED'" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="primary" size="small">进行中</el-tag>
              <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="面试时间" width="160" />

          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <router-link v-if="row.status === 'COMPLETED'" :to="`/personal/interviews/${row.id}/report`">
                <el-button link type="primary">查看复盘报告 →</el-button>
              </router-link>
              <router-link v-else :to="`/personal/interviews/${row.id}/room`">
                <el-button link type="warning">继续作答 →</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { interviewApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'

const loading = ref(true)
const interviews = ref<any[]>([])

const getModeText = (mode: string) => {
  const map: Record<string, string> = {
    TECHNICAL: '技术专项',
    COMPREHENSIVE: '综合模拟',
    PROJECT_DEEP_DIVE: '项目深挖',
    BEHAVIORAL: '行为面试',
    STRESS: '压力训练'
  }
  return map[mode] || mode
}

onMounted(async () => {
  loading.value = true
  try {
    const res: any = await interviewApi.listInterviews()
    interviews.value = res || []
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.interviews-list-page {
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

.interviews-table-card {
  padding: 24px;
}
</style>
