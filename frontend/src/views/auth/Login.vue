<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Left Visual Hero Column (Strict 60% Width) -->
      <div class="auth-hero">
        <div class="hero-top-logo">
          <div class="logo-icon-wrap">
            <el-icon :size="22" color="#FFFFFF"><Monitor /></el-icon>
          </div>
          <div class="logo-text-wrap">
            <span class="logo-title">智面舱</span>
            <span class="logo-subtitle">AI Interview Hub</span>
          </div>
        </div>

        <div class="hero-center-content">
          <div class="hero-badge">AI 赋能 · 职业成长 · 更好你的自己</div>
          <h1 class="hero-headline">
            面向未来的职业能力<br />
            从每一次模拟面试开始
          </h1>
          <p class="hero-subtext">
            精准人岗匹配模型、动态技术深度追问与胜任力雷达诊断，助你在理想的职场舞台上遇见更出色的自己。
          </p>

          <!-- 3 Feature Highlight Cards with Icons -->
          <div class="hero-features-list">
            <div class="h-feature-item">
              <div class="h-icon-box">
                <el-icon :size="18"><Cpu /></el-icon>
              </div>
              <div class="h-text-box">
                <strong>精准 AI 考官问答</strong>
                <p>还原一线名企技术深度追问与多轮答辩</p>
              </div>
            </div>

            <div class="h-feature-item">
              <div class="h-icon-box">
                <el-icon :size="18"><TrendCharts /></el-icon>
              </div>
              <div class="h-text-box">
                <strong>全方位雷达诊断反馈</strong>
                <p>Rubric 评分证据体系，直击薄弱知识点盲区</p>
              </div>
            </div>

            <div class="h-feature-item">
              <div class="h-icon-box">
                <el-icon :size="18"><Trophy /></el-icon>
              </div>
              <div class="h-text-box">
                <strong>显著提升职场竞争力</strong>
                <p>个性化定制学习任务与专项高频考点演练</p>
              </div>
            </div>
          </div>
        </div>

        <div class="hero-footer-quote">
          <span>“让每一次准备，都离理想 Offer 更近一步。”</span>
        </div>
      </div>

      <!-- Right Form Column (Strict 40% Width) -->
      <div class="auth-form-column">
        <div class="form-wrapper">
          <div class="form-header">
            <h2 class="form-title">欢迎登录</h2>
            <p class="form-desc">根据账号角色自动分流至求职者、企业或管理后台</p>
          </div>

          <!-- Recently Used Accounts (saved locally, password never stored) -->
          <div v-if="accountHistory.length" class="history-card">
            <div class="history-head">
              <span class="history-label">上次登录账号（点击一键填入）：</span>
              <span class="history-clear" @click="clearHistory">清空</span>
            </div>
            <div class="pills-grid">
              <span
                v-for="acc in accountHistory"
                :key="acc"
                class="quick-pill history-pill"
                :title="acc"
                @click="fillHistoryAccount(acc)"
              >
                {{ acc }}
              </span>
            </div>
          </div>

          <!-- Quick Autofill Demo Accounts -->
          <div class="demo-pills-card">
            <span class="demo-label">⚡ 快捷填入演示账号：</span>
            <div class="pills-grid">
              <span class="quick-pill pill-student" @click="fillAccount('student@example.com', '123456')">求职学生</span>
              <span class="quick-pill pill-owner" @click="fillAccount('owner@example.com', '123456')">企业创建人</span>
              <span class="quick-pill pill-hr" @click="fillAccount('hr@example.com', '123456')">招聘HR</span>
              <span class="quick-pill pill-interviewer" @click="fillAccount('interviewer@example.com', '123456')">技术面试官</span>
            </div>
          </div>

          <!-- Tabs: 账号密码登录 vs 手机验证码登录 -->
          <div class="auth-tabs">
            <span
              :class="['tab-btn', { active: loginType === 'account' }]"
              @click="loginType = 'account'"
            >
              账号密码登录
            </span>
            <span
              :class="['tab-btn', { active: loginType === 'sms' }]"
              @click="loginType = 'sms'"
            >
              手机验证码登录
            </span>
          </div>

          <!-- Form Area -->
          <el-form :model="loginForm" class="login-inputs-form" @submit.prevent="handleLogin">
            <!-- Account mode -->
            <template v-if="loginType === 'account'">
              <el-form-item>
                <el-input
                  v-model="loginForm.account"
                  name="username"
                  autocomplete="username"
                  placeholder="请输入手机号或邮箱"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>

              <el-form-item>
                <el-input
                  ref="passwordInputRef"
                  v-model="loginForm.password"
                  type="password"
                  name="password"
                  autocomplete="current-password"
                  placeholder="请输入登录密码"
                  prefix-icon="Lock"
                  show-password
                  size="large"
                />
              </el-form-item>
            </template>

            <!-- SMS mode -->
            <template v-else>
              <el-form-item>
                <el-input
                  v-model="smsForm.phone"
                  placeholder="请输入注册手机号"
                  prefix-icon="Iphone"
                  size="large"
                />
              </el-form-item>

              <el-form-item>
                <div class="sms-code-row">
                  <el-input
                    v-model="smsForm.code"
                    placeholder="请输入6位短信验证码"
                    prefix-icon="Key"
                    size="large"
                  />
                  <el-button size="large" class="send-sms-btn" @click="handleSendCode">
                    {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
                  </el-button>
                </div>
              </el-form-item>
            </template>

            <div class="form-extra-row">
              <el-checkbox v-model="loginForm.remember_me">记住登录状态</el-checkbox>
              <router-link to="/forgot-password" class="forgot-link">忘记密码？</router-link>
            </div>

            <el-button
              type="primary"
              class="login-submit-btn"
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              立即登录
            </el-button>
          </el-form>

          <div class="form-bottom-links">
            <span>还没有智面舱账号？</span>
            <router-link to="/register" class="register-cta">立即免费注册</router-link>
            <span class="link-divider">|</span>
            <router-link to="/admin/login" class="admin-link">平台治理入口</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor, Cpu, TrendCharts, Trophy, Iphone, Key } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const loginType = ref<'account' | 'sms'>('account')
const countdown = ref(0)

const loginForm = reactive({
  account: '',
  password: '',
  remember_me: true
})

const smsForm = reactive({
  phone: '13800138001',
  code: '123456'
})

/* ---------- 本地账号历史（仅存账号，绝不存密码） ---------- */
const ACCOUNT_HISTORY_KEY = 'zh_login_accounts'
const ACCOUNT_HISTORY_MAX = 5
const accountHistory = ref<string[]>([])
const passwordInputRef = ref()

const loadAccountHistory = (): string[] => {
  try {
    const raw = localStorage.getItem(ACCOUNT_HISTORY_KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list.filter((x) => typeof x === 'string') : []
  } catch {
    return []
  }
}

const saveAccountHistory = (account: string) => {
  const acc = account.trim()
  if (!acc) return
  const list = [acc, ...accountHistory.value.filter((x) => x !== acc)].slice(0, ACCOUNT_HISTORY_MAX)
  accountHistory.value = list
  localStorage.setItem(ACCOUNT_HISTORY_KEY, JSON.stringify(list))
}

const fillHistoryAccount = async (account: string) => {
  loginType.value = 'account'
  loginForm.account = account
  loginForm.password = ''
  await nextTick()
  passwordInputRef.value?.focus()
}

const clearHistory = () => {
  accountHistory.value = []
  localStorage.removeItem(ACCOUNT_HISTORY_KEY)
  ElMessage.success('已清空本地登录账号记录')
}

onMounted(() => {
  accountHistory.value = loadAccountHistory()
  // 自动回填最近一次登录的账号；密码留给浏览器密码管理器/用户手动输入
  if (accountHistory.value.length) {
    loginForm.account = accountHistory.value[0]
  }
})

const fillAccount = (account: string, pwd: string) => {
  loginType.value = 'account'
  loginForm.account = account
  loginForm.password = pwd
  ElMessage.info(`已填入 ${account}，密码已预填`)
}

const handleSendCode = () => {
  if (countdown.value > 0) return
  if (!smsForm.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  countdown.value = 60
  smsForm.code = '123456'
  ElMessage.success('验证码已发送 (演示验证码为 123456)')
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

const handleLogin = async () => {
  const account = loginType.value === 'account' ? loginForm.account : smsForm.phone
  const password = loginType.value === 'account' ? loginForm.password : smsForm.code

  if (!account || !password) {
    ElMessage.warning('请填写登录凭证')
    return
  }

  loading.value = true
  try {
    const res: any = await authStore.login({ account, password })
    // 仅保存账号用于下次一键填入，密码不写入本地
    saveAccountHistory(account)
    ElMessage.success('登录成功，正在进入工作台')

    const redirect = route.query.redirect as string
    if (redirect) {
      router.push(redirect)
      return
    }

    if (res?.account_type === 'ADMIN') {
      router.push('/admin/dashboard')
    } else if (res?.account_type === 'ENTERPRISE') {
      router.push('/enterprise/dashboard')
    } else {
      router.push('/personal/dashboard')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '账号或密码错误，请核对')
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
  padding: 40px 24px;
  background-color: var(--zh-bg);
}

.auth-container {
  width: 100%;
  max-width: 1140px;
  min-height: 640px;
  background: #FFFFFF;
  border-radius: var(--zh-radius-box);
  border: 1px solid var(--zh-border);
  box-shadow: 0 16px 40px rgba(15, 35, 71, 0.08);
  display: grid;
  grid-template-columns: 1.4fr 1fr; /* Strict 60% : 40% ratio */
  overflow: hidden;
}

/* Left Hero: 60% Royal Indigo Visual Column */
.auth-hero {
  background: linear-gradient(145deg, #1E3A8A 0%, #172554 60%, #0F172A 100%);
  color: #FFFFFF;
  padding: 48px 44px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
}

.hero-top-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: #2563EB;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
}

.logo-text-wrap {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 18px;
  font-weight: 800;
  color: #FFFFFF;
  line-height: 1.1;
}

.logo-subtitle {
  font-size: 11px;
  color: #93C5FD;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.hero-center-content {
  margin: 32px 0;
}

.hero-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  color: #BFDBFE;
  margin-bottom: 20px;
}

.hero-headline {
  font-size: 32px;
  font-weight: 800;
  line-height: 1.3;
  margin-bottom: 16px;
  letter-spacing: -0.02em;
  color: #FFFFFF;
}

.hero-subtext {
  font-size: 14px;
  color: #CBD5E1;
  line-height: 1.6;
  max-width: 480px;
  margin-bottom: 32px;
}

.hero-features-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.h-feature-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(255, 255, 255, 0.06);
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.h-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.4);
  color: #93C5FD;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.h-text-box strong {
  font-size: 14px;
  color: #FFFFFF;
  display: block;
}
.h-text-box p {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 2px;
}

.hero-footer-quote {
  font-size: 13px;
  color: #93C5FD;
  font-style: italic;
  border-left: 2px solid #3B82F6;
  padding-left: 12px;
}

/* Right Form: 40% Column */
.auth-form-column {
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #FFFFFF;
}

.form-wrapper {
  max-width: 380px;
  margin: 0 auto;
  width: 100%;
}

.form-header {
  margin-bottom: 20px;
}

.form-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.form-desc {
  font-size: 13px;
  color: var(--zh-text-muted);
}

/* Recently Used Accounts Card */
.history-card {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.history-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.history-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #1D4ED8;
}

.history-clear {
  font-size: 11px;
  color: var(--zh-text-muted);
  cursor: pointer;
  transition: color 0.15s;
}
.history-clear:hover {
  color: #DC2626;
}

.history-pill {
  background: #FFFFFF;
  color: #1D4ED8;
  border: 1px solid #93C5FD;
  max-width: 175px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Demo Pills Card */
.demo-pills-card {
  background: var(--zh-sub-bg);
  border: 1px solid var(--zh-border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 20px;
}

.demo-label {
  display: block;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--zh-text-muted);
  margin-bottom: 6px;
}

.pills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quick-pill {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.12s;
}

.pill-student { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
.pill-owner { background: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }
.pill-hr { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.pill-interviewer { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

.quick-pill:hover {
  filter: brightness(0.95);
  transform: translateY(-1px);
}

/* Tabs */
.auth-tabs {
  display: flex;
  border-bottom: 2px solid var(--zh-border);
  margin-bottom: 20px;
  gap: 24px;
}

.tab-btn {
  font-size: 14.5px;
  font-weight: 500;
  color: var(--zh-text-muted);
  padding-bottom: 8px;
  cursor: pointer;
  position: relative;
  transition: color 0.15s;
}

.tab-btn:hover, .tab-btn.active {
  color: var(--zh-primary);
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--zh-primary);
  border-radius: 2px;
}

.sms-code-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.send-sms-btn {
  white-space: nowrap;
  font-size: 13px !important;
}

.form-extra-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  font-size: 13px;
}

.forgot-link {
  color: var(--zh-text-muted);
  transition: color 0.15s;
}
.forgot-link:hover {
  color: var(--zh-primary);
}

.login-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px !important;
  font-weight: 600 !important;
}

.form-bottom-links {
  text-align: center;
  font-size: 13px;
  color: var(--zh-text-muted);
  margin-top: 24px;
}

.register-cta {
  color: var(--zh-primary);
  font-weight: 600;
  margin-left: 4px;
}

.link-divider {
  margin: 0 8px;
  color: var(--zh-border);
}

.admin-link {
  color: var(--zh-text-muted);
}
.admin-link:hover {
  color: var(--zh-primary);
}

@media (max-width: 900px) {
  .auth-container {
    grid-template-columns: 1fr;
  }
  .auth-hero {
    display: none;
  }
}
</style>
