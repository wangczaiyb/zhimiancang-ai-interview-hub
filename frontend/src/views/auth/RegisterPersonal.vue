<template>
  <div class="auth-page">
    <div class="register-card">
      <div class="form-header">
        <h2 class="title">创建个人求职账号</h2>
        <p class="subtitle">注册完成后即可进入个人求职工作台与 AI 模拟面试仓</p>
      </div>

      <el-form :model="form" class="auth-form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="form.name"
            placeholder="请输入用户名（虚拟名称）"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.email"
            placeholder="请输入电子邮箱 (如 student@example.com)"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="设置登录密码 (至少6位)"
            prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="确认登录密码"
            prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="form.agreed">
            我已阅读并同意 <a href="javascript:void(0);" class="link-primary">《用户服务协议》</a> 与 <a href="javascript:void(0);" class="link-primary">《个人信息隐私保护政策》</a>
          </el-checkbox>
        </el-form-item>

        <el-button
          type="primary"
          class="submit-btn"
          size="large"
          :loading="loading"
          @click="handleRegister"
        >
          立即注册并开始引导
        </el-button>
      </el-form>

      <div class="form-footer">
        已有账号？<router-link to="/login" class="link-primary">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Message, Lock, User } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const form = reactive({
  name: '',
  email: '',
  password: '',
  confirm_password: '',
  agreed: true
})

const handleRegister = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请填写用户名（虚拟名称）')
    return
  }
  if (!form.email || !form.password) {
    ElMessage.warning('请填写邮箱和密码')
    return
  }
  if (form.password !== form.confirm_password) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  if (!form.agreed) {
    ElMessage.warning('请阅读并勾选用户协议')
    return
  }

  loading.value = true
  try {
    const res: any = await authApi.registerPersonal(form)
    authStore.setAuth(res.access_token, {
      id: res.user_id,
      email: form.email,
      account_type: 'PERSONAL',
      roles: ['PERSONAL_USER'],
      name: res.name
    })
    ElMessage.success('注册成功！进入个人初始偏好引导')
    router.push('/onboarding')
  } catch (e) {
    // Handled by axios interceptor
  } finally {
    loading.value = false
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
  background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
}

.register-card {
  width: 100%;
  max-width: 480px;
  background: #FFFFFF;
  border-radius: var(--zh-radius-xl);
  padding: 40px 36px;
  box-shadow: var(--zh-shadow);
  border: 1px solid var(--zh-border-light);
}

.form-header {
  margin-bottom: 24px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.subtitle {
  font-size: 13px;
  color: var(--zh-text-muted);
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-weight: 600;
  margin-top: 8px;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: var(--zh-text-muted);
}

.link-primary {
  color: var(--zh-primary);
  font-weight: 600;
}
</style>
