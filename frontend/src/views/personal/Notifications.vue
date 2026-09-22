<template>
  <div class="notifications-page">
    <div class="header-box zh-card">
      <div class="header-content">
        <div>
          <h2 class="title">消息与通知中心</h2>
          <p class="subtitle">汇集企业面试邀请、招聘推进状态、系统提醒与学习关怀</p>
        </div>
        <el-button :loading="markingAll" @click="markAllRead">全部已读</el-button>
      </div>
    </div>

    <StateContainer :loading="loading" :empty="!loading && notis.length === 0" empty-text="暂无新消息通知">
      <div class="notis-list">
        <div
          v-for="n in notis"
          :key="n.id"
          :class="['noti-card zh-card', { unread: !n.read }]"
          @click="markRead(n)"
        >
          <div class="noti-icon" :class="getIconClass(n.type)">
            <el-icon :size="20"><Bell /></el-icon>
          </div>
          <div class="noti-main">
            <div class="noti-title-row">
              <h4 class="n-title">{{ n.title }}</h4>
              <span class="n-time">{{ n.created_at }}</span>
            </div>
            <p class="n-desc">{{ n.content }}</p>
            <div v-if="n.link" class="n-action">
              <router-link :to="n.link">
                <el-button link type="primary">立即处理 →</el-button>
              </router-link>
            </div>
          </div>
          <div v-if="!n.read" class="unread-dot"></div>
        </div>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { personalApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'

const loading = ref(true)
const markingAll = ref(false)
const notis = ref<any[]>([])

const loadNotis = async () => {
  loading.value = true
  try {
    const res: any = await personalApi.getNotifications()
    notis.value = res || []
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
}

const markAllRead = async () => {
  markingAll.value = true
  try {
    await personalApi.markAllNotificationsRead()
    ElMessage.success('全部消息已标记为已读')
    loadNotis()
  } catch (e) {
    // handled
  } finally {
    markingAll.value = false
  }
}

const markRead = async (n: any) => {
  if (!n.read) {
    n.read = true
    await personalApi.markNotificationRead(n.id)
  }
}

const getIconClass = (type: string) => {
  if (type === 'INVITATION') return 'bg-amber'
  if (type === 'APPLICATION_PROGRESS') return 'bg-blue'
  return 'bg-purple'
}

onMounted(() => {
  loadNotis()
})
</script>

<style scoped>
.notifications-page {
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

.notis-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.noti-card {
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  cursor: pointer;
}

.noti-card.unread {
  background: #FAFCFF;
  border-left: 4px solid var(--zh-primary);
}

.noti-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bg-amber { background: #FFFBEB; color: #F59E0B; }
.bg-blue { background: #EFF6FF; color: #2563EB; }
.bg-purple { background: #F5F3FF; color: #8B5CF6; }

.noti-main {
  flex: 1;
}

.noti-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.n-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.n-time {
  font-size: 12px;
  color: var(--zh-text-muted);
}

.n-desc {
  font-size: 13px;
  color: var(--zh-text-body);
  line-height: 1.6;
}

.n-action {
  margin-top: 8px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #EF4444;
  position: absolute;
  top: 20px;
  right: 20px;
}
</style>
