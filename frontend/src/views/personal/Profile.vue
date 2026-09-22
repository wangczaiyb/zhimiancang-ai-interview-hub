<template>
  <div class="profile-page">
    <div class="header-box zh-card">
      <h2 class="title">个人基本资料与求职偏好</h2>
      <p class="subtitle">维护你的基本个人信息，求职意向将直接用于岗位广场智能匹配度计算</p>
    </div>

    <StateContainer :loading="loading" :error="error" @retry="loadProfile">
      <div v-if="profile" class="profile-form-grid">
        <!-- Basic Info Card -->
        <div class="form-card zh-card">
          <h3 class="sec-title">基本学业与身份资料</h3>
          <el-form label-position="top">
            <el-form-item label="姓名">
              <el-input v-model="profile.name" />
            </el-form-item>

            <div class="form-row">
              <el-form-item label="身份类型">
                <el-select v-model="profile.profile_type">
                  <el-option label="在校生 / 应届生" value="STUDENT" />
                  <el-option label="社会求职者" value="EXPERIENCED" />
                </el-select>
              </el-form-item>
              <el-form-item label="最高学历">
                <el-select v-model="profile.education">
                  <el-option label="本科" value="本科" />
                  <el-option label="硕士" value="硕士" />
                  <el-option label="博士" value="博士" />
                  <el-option label="大专" value="大专" />
                </el-select>
              </el-form-item>
            </div>

            <div class="form-row">
              <el-form-item label="毕业院校">
                <el-input v-model="profile.school" />
              </el-form-item>
              <el-form-item label="所学专业">
                <el-input v-model="profile.major" />
              </el-form-item>
            </div>

            <div class="form-row">
              <el-form-item label="毕业年份">
                <el-input-number v-model="profile.graduation_year" :min="2020" :max="2030" />
              </el-form-item>
              <el-form-item label="工作年限">
                <el-input-number v-model="profile.work_years" :min="0" :max="30" />
              </el-form-item>
            </div>

            <el-form-item label="个人简介">
              <el-input v-model="profile.bio" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </div>

        <!-- Career Preferences Card -->
        <div class="form-card zh-card">
          <h3 class="sec-title">求职偏好与期望</h3>
          <el-form label-position="top">
            <el-form-item label="目标岗位名称">
              <el-input v-model="profile.target_job_title" />
            </el-form-item>

            <el-form-item label="期望城市 (多城市以逗号隔开)">
              <el-input v-model="profile.target_cities" />
            </el-form-item>

            <el-form-item label="期望月薪区间 (K)">
              <div class="salary-row">
                <el-input-number v-model="profile.salary_min" :min="5" :max="100" />
                <span>至</span>
                <el-input-number v-model="profile.salary_max" :min="5" :max="100" />
                <span>K / 月</span>
              </div>
            </el-form-item>

            <el-form-item label="当前求职状态">
              <el-select v-model="profile.job_status" style="width: 100%;">
                <el-option label="正在积极找工作 (离校/离职)" value="LOOKING" />
                <el-option label="在职/在读，考虑更好机会" value="OPEN_TO_OFFERS" />
                <el-option label="暂无找工作打算，仅模拟训练" value="NOT_LOOKING" />
              </el-select>
            </el-form-item>

            <div class="save-bar">
              <el-button type="primary" size="large" :loading="saving" @click="handleSave">
                保存全部修改
              </el-button>
            </div>
          </el-form>
        </div>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { personalApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import StateContainer from '@/components/StateContainer.vue'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(true)
const error = ref(false)
const saving = ref(false)
const profile = ref<any>(null)

const loadProfile = async () => {
  loading.value = true
  error.value = false
  try {
    const res: any = await personalApi.getProfile()
    profile.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await personalApi.updateProfile(profile.value)
    // 同步刷新登录用户缓存，保证顶部导航与工作台左侧的目标岗位/姓名即时对齐
    await authStore.fetchCurrentUser()
    ElMessage.success('个人资料与求职偏好已成功更新！')
  } catch (e) {
    // handled
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-box {
  padding: 24px 32px;
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

.profile-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-card {
  padding: 32px;
}

.sec-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 24px;
  border-bottom: 1px solid var(--zh-border-light);
  padding-bottom: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.salary-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.save-bar {
  margin-top: 36px;
}

@media (max-width: 900px) {
  .profile-form-grid { grid-template-columns: 1fr; }
}
</style>
