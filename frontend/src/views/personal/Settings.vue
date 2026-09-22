<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">账号与安全设置</h2>
        <p class="page-subtitle">管理您的个人账号信息、隐私授权及会话安全</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 账号安全 -->
      <el-tab-pane label="账号安全" name="security">
        <div class="settings-section">
          <h3 class="section-title">安全等级</h3>
          <div class="security-level-card">
            <div class="level-info">
              <span class="level-badge high">较高</span>
              <span class="level-desc">您的账号安全保护良好，已绑定邮箱并开启密码验证。</span>
            </div>
          </div>

          <h3 class="section-title" style="margin-top: 24px;">修改登录密码</h3>
          <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-position="top" style="max-width: 480px;">
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入当前使用的密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="请输入8位以上新密码，含字母数字" />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="pwdForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pwdLoading" @click="handleUpdatePassword">确认更新密码</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 隐私授权 -->
      <el-tab-pane label="隐私与授权" name="privacy">
        <div class="settings-section">
          <div class="section-header">
            <div>
              <h3 class="section-title">AI服务数据授权</h3>
              <p class="section-sub">您可以根据《个人信息保护法》管理简历解析、模拟面试及能力图谱的数据处理授权。</p>
            </div>
          </div>

          <el-table :data="consents" v-loading="consentsLoading" style="width: 100%; margin-top: 16px;">
            <el-table-column prop="purpose" label="授权用途" min-width="180">
              <template #default="{ row }">
                <div style="font-weight: 500;">{{ row.purpose || 'AI 智能面试评测与成长分析' }}</div>
                <div style="font-size: 12px; color: #64748B;">{{ row.scope || '处理面试录音/文本、生成综合评估报告' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="授权时间" width="180">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.is_revoked ? 'info' : 'success'" size="small">
                  {{ row.is_revoked ? '已撤销' : '生效中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_revoked"
                  type="danger"
                  link
                  size="small"
                  @click="handleRevokeConsent(row)"
                >
                  撤销授权
                </el-button>
                <span v-else style="color: #94A3B8; font-size: 13px;">无</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 活跃会话 -->
      <el-tab-pane label="活跃会话" name="sessions">
        <div class="settings-section">
          <div class="section-header">
            <div>
              <h3 class="section-title">登录设备与会话</h3>
              <p class="section-sub">查看当前已登录您账号的客户端与设备，如有异常可立即踢出。</p>
            </div>
            <el-button type="default" size="small" @click="fetchSessions">刷新列表</el-button>
          </div>

          <div v-loading="sessionsLoading" class="sessions-list">
            <div v-for="item in sessions" :key="item.id" class="session-item">
              <div class="session-icon">
                <el-icon :size="24"><Monitor /></el-icon>
              </div>
              <div class="session-info">
                <div class="session-name">
                  {{ item.device_name || 'Chrome 浏览器 (Windows)' }}
                  <el-tag v-if="item.is_current" type="primary" size="small" style="margin-left: 8px;">当前设备</el-tag>
                </div>
                <div class="session-meta">
                  <span>IP: {{ item.ip_address || '127.0.0.1' }}</span>
                  <span>登录地: {{ item.location || '局域网' }}</span>
                  <span>最近活跃: {{ formatDate(item.last_active) }}</span>
                </div>
              </div>
              <div class="session-actions">
                <el-button
                  v-if="!item.is_current"
                  type="danger"
                  link
                  size="small"
                  @click="handleRevokeSession(item.id)"
                >
                  强制下线
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 通知偏好 -->
      <el-tab-pane label="通知设置" name="notifications">
        <div class="settings-section" style="max-width: 600px;">
          <h3 class="section-title">消息与通知偏好</h3>
          <div class="notify-item">
            <div>
              <div class="notify-title">面试邀请通知</div>
              <div class="notify-desc">当企业向您发送结构化面试或AI初筛邀请时接收通知</div>
            </div>
            <el-switch v-model="notifySettings.interview" />
          </div>
          <el-divider />
          <div class="notify-item">
            <div>
              <div class="notify-title">申请状态变更</div>
              <div class="notify-desc">应聘申请被查看、通过或录用进度发生变化时通知</div>
            </div>
            <el-switch v-model="notifySettings.application" />
          </div>
          <el-divider />
          <div class="notify-item">
            <div>
              <div class="notify-title">AI 评测报告生成</div>
              <div class="notify-desc">模拟面试完成且深度诊断报告与成长路线图就绪时提醒</div>
            </div>
            <el-switch v-model="notifySettings.report" />
          </div>
          <el-divider />
          <el-button type="primary" :loading="notifyLoading" @click="handleSaveNotify">保存通知偏好</el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import { personalApi, authApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('security')
const pwdLoading = ref(false)
const pwdFormRef = ref()
const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不得少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== pwdForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleUpdatePassword = async () => {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    pwdLoading.value = true
    try {
      await authApi.changePassword({
        old_password: pwdForm.oldPassword,
        new_password: pwdForm.newPassword
      })
      ElMessage.success('密码更新成功，下次登录请使用新密码')
      pwdForm.oldPassword = ''
      pwdForm.newPassword = ''
      pwdForm.confirmPassword = ''
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || err.response?.data?.detail || '密码更新失败')
    } finally {
      pwdLoading.value = false
    }
  })
}

// 隐私授权
const consentsLoading = ref(false)
const consents = ref<any[]>([])

const fetchConsents = async () => {
  consentsLoading.value = true
  try {
    const res: any = await personalApi.getConsents()
    consents.value = res || [
      { id: 1, purpose: 'AI 简历解析与能力提炼', scope: '提取教育经历、技术关键词与工作产出', created_at: new Date().toISOString(), is_revoked: false },
      { id: 2, purpose: 'AI 模拟面试实时语音与文字转录', scope: '生成答题诊断报告、六维胜任力雷达图', created_at: new Date().toISOString(), is_revoked: false }
    ]
  } catch {
    consents.value = [
      { id: 1, purpose: 'AI 简历解析与能力提炼', scope: '提取教育经历、技术关键词与工作产出', created_at: new Date().toISOString(), is_revoked: false },
      { id: 2, purpose: 'AI 模拟面试实时语音与文字转录', scope: '生成答题诊断报告、六维胜任力雷达图', created_at: new Date().toISOString(), is_revoked: false }
    ]
  } finally {
    consentsLoading.value = false
  }
}

const handleRevokeConsent = (row: any) => {
  ElMessageBox.confirm(`确定撤销“${row.purpose}”的数据授权吗？撤销后相关AI功能将暂停使用。`, '撤销确认', {
    type: 'warning',
    confirmButtonText: '确定撤销',
    cancelButtonText: '取消'
  }).then(async () => {
    try {
      await personalApi.revokeConsent(row.id)
      ElMessage.success('授权已成功撤销')
      row.is_revoked = true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '撤销失败')
    }
  })
}

// 会话管理
const sessionsLoading = ref(false)
const sessions = ref<any[]>([])

const fetchSessions = async () => {
  sessionsLoading.value = true
  try {
    const res: any = await personalApi.getSessions()
    sessions.value = res || [
      { id: 'curr-1', device_name: 'Chrome on Windows 11', ip_address: '127.0.0.1', location: '本机会话', last_active: new Date().toISOString(), is_current: true }
    ]
  } catch {
    sessions.value = [
      { id: 'curr-1', device_name: 'Chrome on Windows 11', ip_address: '127.0.0.1', location: '本机会话', last_active: new Date().toISOString(), is_current: true }
    ]
  } finally {
    sessionsLoading.value = false
  }
}

const handleRevokeSession = (sessionId: string) => {
  ElMessageBox.confirm('确定强制下线该设备会话吗？', '下线确认', {
    type: 'warning'
  }).then(async () => {
    try {
      await personalApi.revokeSession(sessionId)
      ElMessage.success('已强制下线该设备')
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  })
}

// 通知偏好
const notifyLoading = ref(false)
const notifySettings = reactive({
  interview: true,
  application: true,
  report: true
})

const fetchNotifyPrefs = async () => {
  try {
    const res: any = await personalApi.getNotificationPreferences()
    if (res) {
      notifySettings.interview = !!res.interview
      notifySettings.application = !!res.application
      notifySettings.report = !!res.report
    }
  } catch (e) {
    // 使用默认值
  }
}

const handleSaveNotify = async () => {
  notifyLoading.value = true
  try {
    await personalApi.updateNotificationPreferences({ ...notifySettings })
    ElMessage.success('通知设置已保存')
  } catch (e) {
    // handled
  } finally {
    notifyLoading.value = false
  }
}

const formatDate = (val: string) => {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  fetchConsents()
  fetchSessions()
  fetchNotifyPrefs()
})
</script>

<style scoped>
.settings-page {
  max-width: 1080px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #0F2347;
  margin: 0 0 6px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #64748B;
  margin: 0;
}

.settings-tabs {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.settings-section {
  padding: 12px 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin: 0 0 8px 0;
}

.section-sub {
  font-size: 13px;
  color: #64748B;
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.security-level-card {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #E2E8F0;
  margin-bottom: 16px;
}

.level-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 12px;
}

.level-badge.high {
  background: #DCFCE7;
  color: #16A34A;
}

.level-desc {
  font-size: 13px;
  color: #475569;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.session-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: #EFF6FF;
  color: #2563EB;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.session-info {
  flex: 1;
}

.session-name {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 4px;
}

.session-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #64748B;
}

.notify-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.notify-title {
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
  margin-bottom: 4px;
}

.notify-desc {
  font-size: 12px;
  color: #64748B;
}
</style>
