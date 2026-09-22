<template>
  <div class="auth-page">
    <div class="card">
      <h2>找回密码</h2>
      <p class="desc">输入注册邮箱获取重置令牌，然后设置新密码</p>

      <el-form label-position="top">
        <!-- 第一步：发送重置令牌 -->
        <el-form-item label="电子邮箱">
          <div class="email-row">
            <el-input v-model="email" placeholder="请输入注册邮箱" size="large" />
            <el-button type="primary" size="large" :loading="sending" @click="handleSend">
              获取重置令牌
            </el-button>
          </div>
        </el-form-item>

        <!-- 第二步：重置密码 -->
        <el-form-item label="重置令牌">
          <el-input v-model="resetToken" placeholder="邮件中的令牌（演示环境自动填入）" size="large" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="请输入新密码（至少6位）" size="large" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="confirmPassword" type="password" show-password placeholder="再次输入新密码" size="large" />
        </el-form-item>

        <el-button type="primary" size="large" style="width: 100%;" :loading="resetting" @click="handleReset">
          重置密码
        </el-button>
      </el-form>

      <div class="footer">
        <router-link to="/login" class="link-primary">← 返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const email = ref('')
const resetToken = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const sending = ref(false)
const resetting = ref(false)

onMounted(() => {
  // 支持从邮件链接 ?token=xxx 直接进入
  const token = route.query.token
  if (token && typeof token === 'string') {
    resetToken.value = token
  }
})

const handleSend = async () => {
  if (!email.value.trim()) {
    ElMessage.warning('请输入注册邮箱')
    return
  }
  sending.value = true
  try {
    const res: any = await authApi.forgotPassword(email.value.trim())
    const token = res?.dev_reset_token
    if (token) {
      resetToken.value = token
      ElMessage.success('开发模式：重置令牌已生成并自动填入，请直接设置新密码')
    } else {
      ElMessage.success('重置令牌已发送至您的邮箱，请查收')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '发送失败，请稍后重试')
  } finally {
    sending.value = false
  }
}

const handleReset = async () => {
  if (!resetToken.value.trim()) {
    ElMessage.warning('请先获取重置令牌')
    return
  }
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('新密码长度不能少于 6 位')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }

  resetting.value = true
  try {
    await authApi.resetPassword({
      token: resetToken.value.trim(),
      new_password: newPassword.value
    })
    ElMessage.success('密码已重置，请使用新密码登录')
    router.push('/login')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '重置失败，请重新获取令牌')
  } finally {
    resetting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: var(--zh-bg);
}
.card {
  width: 100%;
  max-width: 460px;
  background: #FFFFFF;
  border-radius: var(--zh-radius-xl);
  padding: 40px 36px;
  box-shadow: var(--zh-shadow);
  border: 1px solid var(--zh-border-light);
}
h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}
.desc {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin-bottom: 24px;
}
.email-row {
  display: flex;
  gap: 8px;
  width: 100%;
}
.footer {
  text-align: center;
  margin-top: 24px;
}
.link-primary {
  color: var(--zh-primary);
  font-weight: 600;
}
</style>