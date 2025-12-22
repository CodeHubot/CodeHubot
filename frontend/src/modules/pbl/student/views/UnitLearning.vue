<template>
  <div class="unit-learning" v-if="loading">
    <div class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
  </div>
  <div class="unit-learning" v-else-if="currentUnit">
    <!-- 单元导航栏 -->
    <nav class="unit-nav">
      <div class="nav-content">
        <el-button :icon="ArrowLeft" @click="goBack" size="small" link>返回</el-button>
        <div class="unit-info">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: '/pbl/student/courses' }">我的课程</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: `/pbl/student/courses/${courseId.value}` }">{{ courseName }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentUnit.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
      </div>
    </nav>

    <!-- 两栏学习布局 -->
    <div class="learning-layout">
      <!-- 左侧：学习路径与目录 -->
      <div class="left-panel">
        <div class="panel-header custom-tabs-header">
          <el-tabs v-model="leftPanelTab" class="left-panel-tabs">
            <el-tab-pane label="当前任务" name="path"></el-tab-pane>
            <el-tab-pane label="课程目录" name="outline"></el-tab-pane>
          </el-tabs>
        </div>
        
        <div class="panel-content path-content">
          <!-- 视图1：当前任务路径 -->
          <div v-if="leftPanelTab === 'path'" class="learning-steps">
            <div class="path-summary">
              <span class="progress-text">{{ completedSteps }}/{{ learningPath.length }} 完成</span>
              <el-progress :percentage="progressPercentage" :show-text="false" :stroke-width="4" />
            </div>
            
            <div 
              v-for="(step, index) in learningPath" 
              :key="step.id"
              class="step-item"
              :class="{ 
                'active': currentStep?.id === step.id,
                'completed': step.status === 'completed'
              }"
              @click="selectStep(step)"
            >
              <div class="step-indicator">
                <div class="step-line" v-if="index < learningPath.length - 1"></div>
                <div class="step-icon">
                  <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
                  <span v-else>{{ index + 1 }}</span>
                </div>
              </div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-type">
                  <el-tag 
                    size="small" 
                    :type="getStepTypeTag(step.type) || undefined"
                  >
                    {{ getStepTypeName(step.type) }}
                  </el-tag>
                  <el-tag 
                    v-if="step.type === 'task' && step.taskCategory" 
                    size="small" 
                    effect="plain"
                    :type="step.taskCategory === 'group' ? 'warning' : 'info'"
                    style="margin-left: 8px"
                  >
                    {{ step.taskCategory === 'group' ? '小组' : '个人' }}
                  </el-tag>
                  <span class="step-duration" v-if="step.duration">{{ step.duration }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 视图2：课程大纲 -->
          <div v-else class="course-outline">
            <div 
              v-for="unit in courseUnits" 
              :key="unit.id"
              class="outline-item"
              :class="{ 'active': unit.id === currentUnit.id }"
            >
              <div class="outline-status">
                 <el-icon v-if="unit.id === currentUnit.id"><VideoPlay /></el-icon>
                 <div v-else class="status-dot"></div>
              </div>
              <div class="outline-info">
                <div class="outline-title">{{ unit.title }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：动态内容区 -->
      <div class="center-panel">
        <div class="panel-header">
          <h2>
            {{ currentStep?.title || '请选择学习步骤' }}
            <el-tag v-if="currentStep?.status === 'completed'" type="success" effect="dark" size="small" class="ml-2">已完成</el-tag>
          </h2>
          <!-- 手动标记按钮（仅对非任务类型的学习资源有效） -->
          <div class="header-actions" v-if="currentStep && currentStep.type !== 'task'">
             <el-button 
               v-if="currentStep.status !== 'completed'" 
               type="success" 
               plain 
               size="small" 
               @click="manualCompleteStep"
             >
               标记为已完成
             </el-button>
             <el-button 
               v-else 
               type="info" 
               plain 
               size="small" 
               @click="manualUncompleteStep"
             >
               标记为未完成
             </el-button>
          </div>
        </div>
        
        <div class="panel-content main-learning-area" v-if="currentStep">
          <!-- 场景1：视频学习 -->
          <div v-if="currentStep.type === 'video'" class="video-learning">
            <VideoPlayer 
              v-if="!videoLoadError"
              :vid="videoPlayData.videoId"
              :playAuth="videoPlayData.playAuth"
              :source="videoPlayData.source" 
              :cover="videoPlayData.cover"
              :resourceUuid="currentStep.resourceUuid || currentStep.id"
              :autoplay="true"
              :autoPauseInterval="180"
              :enableTracking="true"
              height="100%"
              @ended="handleVideoEnded"
              @auto-pause="handleAutoPause"
            />
            <div v-else class="video-error">
              <el-result icon="error" title="视频加载失败" :sub-title="videoLoadError">
                <template #extra>
                  <el-button type="primary" @click="retryLoadVideo">重试</el-button>
                </template>
              </el-result>
            </div>
          </div>

          <!-- 场景2：文档阅读 -->
          <div v-else-if="currentStep.type === 'document'" class="document-learning">
            <div class="markdown-preview" v-html="renderedDocumentContent"></div>
            <div class="step-actions">
              <el-button 
                type="primary" 
                size="large" 
                @click="completeCurrentStep"
                :disabled="currentStep.status === 'completed'"
              >
                {{ currentStep.status === 'completed' ? '已完成阅读' : '我已阅读完成，下一步' }}
              </el-button>
            </div>
          </div>

          <!-- 场景3：实践任务 -->
          <div v-else-if="currentStep.type === 'task'" class="task-learning">
            <div class="task-detail">
              <div class="task-description">
                <h3>任务描述</h3>
                <p>{{ currentStep.data.description }}</p>
              </div>
              
              <div class="task-requirements">
                <h3>任务要求</h3>
                <ul>
                  <li v-for="(req, idx) in currentStep.data.requirements" :key="idx">{{ req }}</li>
                </ul>
              </div>

              <div class="submission-area">
                <h3>作业提交</h3>
                <el-alert 
                  v-if="currentStep.originalStatus === 'review' || (currentStep.status === 'completed' && !currentStep.data?.score)" 
                  type="info" 
                  :closable="false"
                  style="margin-bottom: 15px;"
                >
                  作业已提交，等待评分。您可以重新提交以更新作业内容。
                </el-alert>
                <el-alert 
                  v-if="currentStep.data?.score" 
                  type="warning" 
                  :closable="false"
                  style="margin-bottom: 15px;"
                >
                  作业已评分（{{ currentStep.data.score }}分）。重新提交将覆盖原有评分。
                </el-alert>
                <el-form label-position="top">
                  <el-form-item label="作业内容">
                    <el-input 
                      v-model="submissionContent" 
                      type="textarea" 
                      :rows="10" 
                      placeholder="请输入你的作业内容"
                      class="fixed-textarea"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button 
                      type="primary" 
                      @click="submitTask" 
                      :loading="submitting"
                    >
                      {{ currentStep.submission && currentStep.submission.content ? '重新提交' : '提交作业' }}
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </div>

          <!-- 场景4：在线测验 -->
          <div v-else-if="currentStep.type === 'quiz'" class="quiz-learning">
            <div class="quiz-container">
              <div v-for="(question, index) in currentStep.data.questions" :key="index" class="quiz-item">
                <div class="question-title">{{ index + 1 }}. {{ question.title }}</div>
                <el-radio-group v-model="quizAnswers[index]" :disabled="currentStep.status === 'completed'">
                  <el-radio 
                    v-for="(option, optIndex) in question.options" 
                    :key="optIndex" 
                    :label="optIndex"
                    class="quiz-option"
                  >
                    {{ option }}
                  </el-radio>
                </el-radio-group>
              </div>
              
              <div class="step-actions">
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="submitQuiz"
                  :loading="submitting"
                  :disabled="currentStep.status === 'completed'"
                >
                  {{ currentStep.status === 'completed' ? '已通过测验' : '提交答案' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <el-empty description="请从左侧选择一个学习步骤开始" />
        </div>
      </div>

      <!-- 右侧：AI助手 (已隐藏) -->
      <!-- <div class="right-panel">
        <ChatPanel />
      </div> -->
    </div>

    <!-- 悬浮AI助手 -->
    <FloatingAIAssistant 
      v-if="showAIAssistant"
      :unit-id="currentUnit?.uuid || ''"
      :course-id="courseId"
      storage-mode="session"
      :enable-server-sync="true"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, ArrowRight, Check, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import FloatingAIAssistant from '../components/FloatingAIAssistant.vue'
import VideoPlayer from '../components/VideoPlayer.vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { 
  getUnitDetail, 
  getCourseDetail, 
  getCourseUnits, 
  trackLearningProgress,
  getUnitResourcesProgress,
  getVideoPlayAuth,
  submitTask as submitTaskAPI,
  resetLearningProgress
} from '../api/student'
import { getPublicConfigs } from '@/modules/device/api/systemConfig'

const router = useRouter()
const route = useRoute()

// 配置 marked 选项
marked.setOptions({
  breaks: true,  // 支持 GitHub 风格的换行
  gfm: true,     // 启用 GitHub Flavored Markdown
  headerIds: true,
  mangle: false
})

// 状态管理
const leftPanelTab = ref('path')
const currentUnit = ref(null)
const courseId = ref('') // 从单元数据中获取
const courseName = ref('') // 从 API 获取
const learningPath = ref([])
const currentStep = ref(null)
const submissionContent = ref('')
const submitting = ref(false)
const quizAnswers = ref({})
const loading = ref(true)

// AI助手配置
const showAIAssistant = ref(true) // 默认显示，从后台配置加载

const courseUnits = ref([])
const previousUnit = ref(null)
const nextUnit = ref(null)

// 加载AI助手配置
const loadAIAssistantConfig = async () => {
  try {
    const response = await getPublicConfigs()
    const configs = response.data || []
    
    // 查找AI助手配置项
    const aiAssistantConfig = configs.find(
      config => config.config_key === 'enable_ai_assistant_in_unit'
    )
    
    if (aiAssistantConfig) {
      // 处理布尔值配置
      if (aiAssistantConfig.config_type === 'boolean') {
        showAIAssistant.value = aiAssistantConfig.config_value === 'true'
      }
    }
  } catch (error) {
    console.error('加载AI助手配置失败:', error)
    // 失败时保持默认值 true，不影响用户体验
  }
}

// 视频播放相关状态
const videoPlayData = ref({
  videoId: '',
  playAuth: '',
  source: '',
  cover: ''
})
const videoLoadError = ref('')

// 从后端API加载单元数据
const loadUnitData = async (unitUuid) => {
  try {
    loading.value = true
    
    // 获取单元详情
    const unitData = await getUnitDetail(unitUuid)
    
    currentUnit.value = {
      id: unitData.id,
      uuid: unitData.uuid,
      title: unitData.title,
      description: unitData.description,
      status: unitData.status,
      order: unitData.order
    }
    
    // 设置课程信息
    if (unitData.course_uuid) {
      courseId.value = unitData.course_uuid
      courseName.value = unitData.course_title || ''
      
      // 获取课程的所有单元列表
      try {
        const units = await getCourseUnits(unitData.course_uuid)
        courseUnits.value = units.map(u => ({
          id: u.id,
          uuid: u.uuid,
          title: u.title,
          status: u.status,
          duration: '', // 可以后续计算
          order: u.order
        }))
        
        // 找到当前单元在列表中的位置
        const currentIndex = courseUnits.value.findIndex(u => u.uuid === unitUuid)
        if (currentIndex > 0) {
          previousUnit.value = courseUnits.value[currentIndex - 1]
        }
        if (currentIndex < courseUnits.value.length - 1) {
          nextUnit.value = courseUnits.value[currentIndex + 1]
        }
      } catch (error) {
        console.error('获取课程单元列表失败:', error)
      }
    }
    
    // 构建学习路径：合并资料和任务，并按 order 字段统一排序
    learningPath.value = []
    
    // 创建临时数组存储所有学习项（资源和任务）
    const allLearningItems = []
    
    // 添加学习资料
    if (unitData.resources && unitData.resources.length > 0) {
      unitData.resources.forEach(resource => {
        const step = {
          id: `resource-${resource.id}`,
          uuid: resource.uuid,
          title: resource.title,
          type: resource.type, // video, document, link
          status: 'locked', // 默认锁定，第一个项设置为 available
          duration: resource.duration ? `${resource.duration}分钟` : '',
          order: resource.order || 0,
          data: {
            url: resource.url,
            content: resource.content,
            cover: resource.video_cover_url,
            description: resource.description,
            video_id: resource.video_id
          }
        }
        allLearningItems.push(step)
      })
    }
    
    // 添加任务
    if (unitData.tasks && unitData.tasks.length > 0) {
      unitData.tasks.forEach(task => {
        const step = {
          id: `task-${task.id}`,
          uuid: task.uuid,
          title: task.title,
          type: 'task',
          taskCategory: task.type, // analysis, coding, design, deployment
          status: 'locked', // 默认锁定，第一个项设置为 available
          duration: task.estimated_time || '',
          order: task.order || 0,
          data: {
            description: task.description,
            requirements: typeof task.requirements === 'string' ? JSON.parse(task.requirements) : (task.requirements || []),
            prerequisites: task.prerequisites
          }
        }
        allLearningItems.push(step)
      })
    }
    
    // 按 order 字段统一排序
    allLearningItems.sort((a, b) => a.order - b.order)
    
    // 所有学习项都设置为可访问
    allLearningItems.forEach(item => {
      if (item.status !== 'completed') {
        item.status = 'available'
      }
    })
    
    // 设置学习路径
    learningPath.value = allLearningItems
    
    // 加载学习进度，更新各步骤的完成状态
    await loadLearningProgress(unitUuid)
    
    loading.value = false
    
  } catch (error) {
    console.error('加载单元数据失败:', error)
    ElMessage.error(error.message || '加载单元数据失败')
    loading.value = false
    // 返回到课程列表
    router.push('/pbl/student/courses')
  }
}

// 以下是保留的硬编码数据，用于开发测试（将被删除）
const _oldSmartHomeUnit1Steps = [
  {
    id: 101,
    title: 'Agent 101：从 ChatGPT 到智能体',
    type: 'video',
    status: 'available',
    duration: '10:00',
    data: {
      url: 'https://player.alicdn.com/video/aliyunmedia.mp4', // 替换为实际视频
      cover: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
      description: '了解什么是 AI Agent（智能体），它与普通聊天机器人的区别，以及 LLM + Memory + Tools + Planning 的核心架构。'
    }
  },
  {
    id: 102,
    title: 'Coze 平台保姆级教程',
    type: 'video',
    status: 'locked',
    duration: '20:00',
    data: {
      url: 'https://player.alicdn.com/video/aliyunmedia.mp4',
      cover: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
    }
  },
  {
    id: 103,
    title: '知识讲义：RTF 提示词框架',
    type: 'document',
    status: 'locked',
    duration: '15分钟',
    data: {
      content: `
        <h2>✍️ 高效 Prompt 编写指南：RTF 框架</h2>
        <p>怎么让 AI 听话？我们需要写好“人设”。推荐使用 <strong>RTF 框架</strong>：</p>
        
        <h3>R (Role) - 角色</h3>
        <p>你是谁？定义 Agent 的身份、背景和性格。</p>
        <p class="example">例：你是一个专业的家庭管家 Jarvis。</p>
        
        <h3>T (Task) - 任务</h3>
        <p>你要做什么？明确 Agent 的主要职责和目标。</p>
        <p class="example">例：你需要根据用户的模糊指令控制家电设备，并给出温馨的反馈。</p>
        
        <h3>F (Format) - 格式</h3>
        <p>你输出什么格式？规定回复的风格、长度或结构。</p>
        <p class="example">例：请用简短、口语化的中文回答，不要长篇大论。</p>
        
        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px;">
          <h4>📌 练习</h4>
          <p>试着为你未来的“智能家居中控”写一段 Prompt，包含以上三个要素。</p>
        </div>
      `
    }
  },
  {
    id: 104,
    title: '实战任务 1.1：Hello World',
    type: 'task',
    taskCategory: 'individual',
    status: 'locked',
    duration: '30分钟',
    data: {
      description: '访问 Coze 官网，注册账号并创建一个全新的 Bot，命名为 Jarvis-Lite（或你喜欢的名字）。',
      requirements: [
        '完成 Coze 账号注册',
        '创建 Bot，填写名称和简介',
        '生成并设置 Bot 头像',
        '提交 Bot ID 或截图'
      ]
    }
  },
  {
    id: 105,
    title: '实战任务 1.2：注入灵魂',
    type: 'task',
    taskCategory: 'group',
    status: 'locked',
    duration: '45分钟',
    data: {
      description: '使用 RTF 框架编写 Prompt，并填入“人设与回复逻辑”区域。让你的 Agent 知道自己是管家，而不是百科全书。',
      requirements: [
        '编写包含 Role, Task, Format 的 Prompt',
        '设定“意图识别”技能',
        '在右侧预览窗口进行不少于 3 轮的对话测试',
        '提交 Prompt 内容和对话截图'
      ]
    }
  },
  {
    id: 106,
    title: '实战任务 1.3：初次调试',
    type: 'task',
    taskCategory: 'individual',
    status: 'locked',
    duration: '20分钟',
    data: {
      description: '在预览窗口验证人设是否生效。尝试输入“你是谁？”、“把灯打开”等指令，观察它的反应。',
      requirements: [
        '测试自我介绍',
        '测试设备控制指令（模拟）',
        '测试闲聊话题（验证约束条件）',
        '提交测试报告'
      ]
    }
  }
]

// 计算属性
const completedSteps = computed(() => {
  return learningPath.value.filter(s => s.status === 'completed').length
})

const progressPercentage = computed(() => {
  if (learningPath.value.length === 0) return 0
  return Math.round((completedSteps.value / learningPath.value.length) * 100)
})

// 渲染文档内容（支持 Markdown 和 HTML）
const renderedDocumentContent = computed(() => {
  if (!currentStep.value || currentStep.value.type !== 'document') {
    return ''
  }
  
  const content = currentStep.value.data.content || ''
  
  if (!content) return '<p class="empty-hint">暂无内容</p>'
  
  try {
    // 统一使用 Markdown 渲染（Markdown 兼容 HTML）
    const rawHtml = marked.parse(content)
    // 使用 DOMPurify 清理 HTML，防止 XSS 攻击
    return DOMPurify.sanitize(rawHtml)
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return '<p class="error-hint">内容渲染失败</p>'
  }
})

// 方法（课程目录不再支持点击跳转）
const switchUnit = (unit) => {
  // 课程目录仅用于展示，不支持跳转
  return
}

const getStepTypeName = (type) => {
  const map = { video: '视频', document: '文档', task: '作业', quiz: '测验' }
  return map[type] || '未知'
}

const getStepTypeTag = (type) => {
  const map = { video: '', document: 'info', task: 'warning', quiz: 'danger' }
  return map[type] || ''
}

const selectStep = async (step) => {
  currentStep.value = step
  // 加载之前的提交内容（如果有）
  if (step.type === 'task') {
    if (step.submission && step.submission.content) {
      submissionContent.value = step.submission.content
    } else {
      submissionContent.value = '' 
    }
  }
  // 重置测验
  if (step.type === 'quiz') {
    quizAnswers.value = {}
  }
  
  // 如果是视频类型，加载视频播放数据
  if (step.type === 'video') {
    await loadVideoPlayData(step)
  }
}

// 检查是否所有步骤都已完成
const checkAllStepsCompleted = async () => {
  const allCompleted = learningPath.value.every(s => s.status === 'completed')
  if (allCompleted) {
    ElMessage.success('恭喜！本单元所有内容已完成')
    
    // 记录单元完成状态
    try {
      await trackLearningProgress({
        course_uuid: courseId.value,
        unit_uuid: currentUnit.value.uuid,
        progress_type: 'unit_complete',
        progress_value: 100,
        time_spent: 0
      })
      
      // 更新当前单元的状态为已完成
      if (currentUnit.value) {
        currentUnit.value.status = 'completed'
      }
      
      // 更新课程大纲中的单元状态
      const unitInList = courseUnits.value.find(u => u.uuid === currentUnit.value.uuid)
      if (unitInList) {
        unitInList.status = 'completed'
      }
      
      // 单元完成提示（不跳转）
      setTimeout(() => {
        ElMessageBox.alert(
          '您已完成本单元的所有学习内容，可以继续复习或返回课程列表。',
          '单元学习完成',
          {
            confirmButtonText: '确定',
            type: 'success'
          }
        )
      }, 1500)
    } catch (error) {
      console.error('记录单元完成状态失败:', error)
      // 不影响用户体验，静默失败
    }
  }
}

// 加载学习进度
const loadLearningProgress = async (unitUuid) => {
  try {
    const progressData = await getUnitResourcesProgress(unitUuid)
    
    // 更新资源完成状态
    if (progressData.resource_progress) {
      Object.keys(progressData.resource_progress).forEach(key => {
        const progress = progressData.resource_progress[key]
        const step = learningPath.value.find(s => s.id === key)
        if (step && progress.status === 'completed') {
          step.status = 'completed'
        } else if (step && step.status !== 'completed') {
          step.status = 'available'
        }
      })
    }
    
    // 更新任务完成状态和提交内容
    if (progressData.task_progress) {
      Object.keys(progressData.task_progress).forEach(key => {
        const progress = progressData.task_progress[key]
        const step = learningPath.value.find(s => s.id === key)
        if (step) {
          // 保存提交内容到步骤数据中
          step.submission = progress.submission
          step.score = progress.score
          step.feedback = progress.feedback
          step.originalStatus = progress.status  // 保存原始状态用于区分 review 和 completed
          
          // 如果任务数据对象不存在，创建它
          if (!step.data) {
            step.data = {}
          }
          // 同时保存到 data 对象中，确保模板中能访问到
          step.data.score = progress.score
          step.data.feedback = progress.feedback
          
          // review 状态（已提交等待评分）和 completed 状态都显示为已完成
          if (progress.status === 'completed' || progress.status === 'review') {
            step.status = 'completed'
          } else if (step.status !== 'completed') {
            step.status = 'available'
          }
        }
      })
    }
    
    // 确保所有未完成的步骤都设置为可访问
    learningPath.value.forEach(step => {
      if (step.status !== 'completed') {
        step.status = 'available'
      }
    })
  } catch (error) {
    console.error('加载学习进度失败:', error)
    // 不显示错误消息，静默失败
  }
}

// 记录学习进度到后端
const saveProgress = async (step, progressType, progressValue = 100) => {
  try {
    const progressData = {
      course_uuid: courseId.value,
      unit_uuid: currentUnit.value.uuid,
      progress_type: progressType,
      progress_value: progressValue,
      time_spent: 0
    }
    
    // 判断是资源还是任务
    if (step.type === 'task') {
      progressData.task_uuid = step.uuid
    } else {
      progressData.resource_uuid = step.uuid
    }
    
    await trackLearningProgress(progressData)
  } catch (error) {
    console.error('保存学习进度失败:', error)
    // 不影响用户体验，静默失败
  }
}

// 加载视频播放数据
const loadVideoPlayData = async (step) => {
  try {
    videoLoadError.value = ''
    
    // 如果有阿里云视频ID，则获取播放凭证
    if (step.data.video_id) {
      const authData = await getVideoPlayAuth(step.uuid)
      videoPlayData.value = {
        videoId: authData.video_id,
        playAuth: authData.play_auth,
        source: '',  // 使用阿里云播放时不需要source
        cover: step.data.cover || authData.video_meta?.cover_url || ''
      }
    } else {
      // 使用普通视频URL
      videoPlayData.value = {
        videoId: '',
        playAuth: '',
        source: step.data.url || '',
        cover: step.data.cover || ''
      }
    }
  } catch (error) {
    console.error('加载视频播放数据失败:', error)
    videoLoadError.value = error.message || '视频加载失败，请重试'
  }
}

// 重试加载视频
const retryLoadVideo = async () => {
  if (currentStep.value && currentStep.value.type === 'video') {
    await loadVideoPlayData(currentStep.value)
  }
}

// 视频播放结束处理
const handleVideoEnded = async () => {
  if (currentStep.value.status !== 'completed') {
    currentStep.value.status = 'completed'
    ElMessage.success('视频观看完成！')
    
    // 保存进度到后端
    await saveProgress(currentStep.value, 'video_watch', 100)
    
    checkAllStepsCompleted()
  }
}

// 处理视频自动暂停
const handleAutoPause = (data) => {
  console.log('视频自动暂停:', data)
  ElMessageBox.alert(
    '您已连续观看3分钟，建议休息一下，整理思路或做些笔记。点击"继续学习"可恢复播放。',
    '💡 温馨提示',
    {
      confirmButtonText: '继续学习',
      type: 'info',
      center: true
    }
  )
}

// 文档阅读完成处理
const completeCurrentStep = async () => {
  if (currentStep.value.status !== 'completed') {
    currentStep.value.status = 'completed'
    
    // 保存进度到后端
    await saveProgress(currentStep.value, 'document_read', 100)
    
    checkAllStepsCompleted()
    
    // 自动跳转到下一步
    const currentIndex = learningPath.value.findIndex(s => s.id === currentStep.value.id)
    if (currentIndex < learningPath.value.length - 1) {
      setTimeout(() => {
        selectStep(learningPath.value[currentIndex + 1])
      }, 1000)
    }
  }
}

// 提交作业处理
const submitTask = async () => {
  if (!submissionContent.value.trim()) {
    ElMessage.warning('请输入作业内容')
    return
  }
  
  submitting.value = true
  try {
    // 调用真实的任务提交API
    const result = await submitTaskAPI(currentStep.value.uuid, {
      content: submissionContent.value,
      submitted_at: new Date().toISOString()
    })
    
    // 更新当前步骤状态为已完成（提交后状态为 review，也视为完成）
    currentStep.value.status = 'completed'
    currentStep.value.originalStatus = 'review'  // 保存原始状态
    
    // 更新当前步骤的提交记录，保存刚才提交的内容
    if (!currentStep.value.submission) {
      currentStep.value.submission = {}
    }
    currentStep.value.submission.content = submissionContent.value
    currentStep.value.submission.submitted_at = new Date().toISOString()
    
    // 清空评分信息（重新提交后需要重新评分）
    currentStep.value.score = null
    currentStep.value.feedback = null
    if (!currentStep.value.data) {
      currentStep.value.data = {}
    }
    currentStep.value.data.score = null
    currentStep.value.data.feedback = null
    
    // 同时保存学习进度记录
    await saveProgress(currentStep.value, 'task_submit', 100)
    
    ElMessage.success(result.message || '作业提交成功！')
    checkAllStepsCompleted()
    
    // 重新加载学习进度，获取最新的评分等信息
    await loadLearningProgress(currentUnit.value.uuid)
    
    // 重新加载进度后，同步更新提交内容显示
    // currentStep 是对 learningPath 中对象的引用，所以 submission 已经被更新
    if (currentStep.value.submission && currentStep.value.submission.content) {
      submissionContent.value = currentStep.value.submission.content
    }
  } catch (error) {
    console.error('作业提交失败:', error)
    ElMessage.error(error.message || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 提交测验处理
const submitQuiz = async () => {
  if (Object.keys(quizAnswers.value).length < currentStep.value.data.questions.length) {
    ElMessage.warning('请回答所有问题')
    return
  }

  submitting.value = true
  // 模拟API验证
  await new Promise(resolve => setTimeout(resolve, 800))
  submitting.value = false

  // 验证答案 (这里简化处理，实际应由后端验证)
  let allCorrect = true
  currentStep.value.data.questions.forEach((q, idx) => {
    if (quizAnswers.value[idx] !== q.answer) {
      allCorrect = false
    }
  })

  if (allCorrect) {
    currentStep.value.status = 'completed'
    ElMessage.success('恭喜！全部回答正确')
    checkAllStepsCompleted()
  } else {
    ElMessage.error('有题目回答错误，请重试')
  }
}

// 手动标记完成
const manualCompleteStep = async () => {
  if (currentStep.value) {
    currentStep.value.status = 'completed'
    
    // 根据步骤类型确定进度类型
    let progressType = 'resource_view'
    if (currentStep.value.type === 'video') {
      progressType = 'video_watch'
    } else if (currentStep.value.type === 'document') {
      progressType = 'document_read'
    } else if (currentStep.value.type === 'task') {
      progressType = 'task_submit'
    }
    
    // 保存进度到后端
    await saveProgress(currentStep.value, progressType, 100)
    
    ElMessage.success('已手动标记为完成')
    checkAllStepsCompleted()
  }
}

// 手动取消完成
const manualUncompleteStep = async () => {
  if (currentStep.value) {
    try {
      // 调用后端API删除学习进度记录
      const params = {}
      if (currentStep.value.type === 'task') {
        params.task_uuid = currentStep.value.uuid
      } else {
        params.resource_uuid = currentStep.value.uuid
      }
      
      await resetLearningProgress(params)
      
      // 更新前端状态
      currentStep.value.status = 'available'
      ElMessage.success('已撤销完成状态')
      
      // 重新加载学习进度以确保数据同步
      await loadLearningProgress(currentUnit.value.uuid)
    } catch (error) {
      console.error('撤销完成状态失败:', error)
      ElMessage.error(error.message || '操作失败，请重试')
    }
  }
}

const goBack = () => router.push(`/pbl/student/courses/${courseId.value}`)
const goToUnit = (unitIdOrUuid) => router.push(`/pbl/student/units/${unitIdOrUuid}`)

onMounted(async () => {
  const unitId = route.params.uuid

  // 加载AI助手配置
  await loadAIAssistantConfig()

  // 从后端API加载单元数据
  await loadUnitData(unitId)

  // 默认选中第一个未完成的步骤，如果都完成了则选择第一个
  if (learningPath.value.length > 0) {
    const firstIncomplete = learningPath.value.find(s => s.status !== 'completed')
    if (firstIncomplete) {
      selectStep(firstIncomplete)
    } else {
      // 如果都完成了，选择第一个
      selectStep(learningPath.value[0])
    }
  }
})
</script>

<style scoped>
.unit-learning {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.unit-nav {
  background: white;
  padding: 8px 16px;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  height: 48px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.nav-content {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.unit-info {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.unit-info h1 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.learning-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 0;
  overflow: hidden;
}

.left-panel,
.center-panel,
.right-panel {
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #e5e7eb;
}

.right-panel {
  border-right: none;
}

.panel-header {
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 48px;
  box-sizing: border-box;
}

.panel-header h2 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.custom-tabs-header {
  padding: 0 16px;
}

.left-panel-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.left-panel-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

.progress-text {
  font-size: 12px;
  color: #64748b;
}

.path-summary {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.path-summary .el-progress {
  margin-top: 8px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

/* 课程目录样式 */
.course-outline {
  padding: 0;
}

.outline-item {
  display: flex;
  padding: 16px;
  transition: all 0.2s;
  border-bottom: 1px solid #f1f5f9;
}

.outline-item.active {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.outline-status {
  width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.outline-item.active .outline-status {
  color: #3b82f6;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
}

.outline-info {
  flex: 1;
}

.outline-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

/* 学习路径样式 */
.path-content {
  padding: 0;
}

.step-item {
  display: flex;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f1f5f9;
}

.step-item:hover {
  background: #f8fafc;
}

.step-item.active {
  background: #eff6ff;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 12px;
  position: relative;
  width: 24px;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  z-index: 2;
}

.step-item.active .step-icon {
  background: #3b82f6;
  color: white;
}

.step-item.completed .step-icon {
  background: #10b981;
  color: white;
}

.step-line {
  position: absolute;
  top: 24px;
  bottom: -24px; /* Extend to next item */
  width: 2px;
  background: #e2e8f0;
  z-index: 1;
}

.step-item:last-child .step-line {
  display: none;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 4px;
}

.step-type {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-duration {
  font-size: 12px;
  color: #94a3b8;
}

/* 中间区域样式 */
.main-learning-area {
  padding: 0;
  background: #fff;
  overflow: auto;
}

.video-learning {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.learning-tips {
  margin-top: 16px;
}

.document-learning {
  height: 100%;
  overflow: auto;
  padding: 20px;
}

/* Markdown 预览样式 - 完全复制自编辑器 */
.markdown-preview {
  max-width: 900px;
  margin: 0 auto;
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  word-wrap: break-word;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3),
.markdown-preview :deep(h4),
.markdown-preview :deep(h5),
.markdown-preview :deep(h6) {
  margin: 24px 0 16px;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-preview :deep(h1) {
  font-size: 32px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
}

.markdown-preview :deep(h2) {
  font-size: 28px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
}

.markdown-preview :deep(h3) {
  font-size: 24px;
}

.markdown-preview :deep(h4) {
  font-size: 20px;
}

.markdown-preview :deep(h5) {
  font-size: 18px;
}

.markdown-preview :deep(h6) {
  font-size: 16px;
}

.markdown-preview :deep(p) {
  margin: 16px 0;
}

.markdown-preview :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-preview :deep(a:hover) {
  text-decoration: underline;
}

.markdown-preview :deep(img) {
  max-width: 100%;
  height: auto;
  margin: 16px 0;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.markdown-preview :deep(code) {
  padding: 2px 6px;
  background: #f5f7fa;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 14px;
  color: #e83e8c;
}

.markdown-preview :deep(pre) {
  margin: 16px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-preview :deep(pre code) {
  padding: 0;
  background: none;
  color: inherit;
}

.markdown-preview :deep(blockquote) {
  margin: 16px 0;
  padding: 12px 20px;
  background: #f5f7fa;
  border-left: 4px solid #409eff;
  color: #606266;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  margin: 16px 0;
  padding-left: 28px;
}

.markdown-preview :deep(li) {
  margin: 8px 0;
}

.markdown-preview :deep(table) {
  width: 100%;
  margin: 16px 0;
  border-collapse: collapse;
}

.markdown-preview :deep(table th),
.markdown-preview :deep(table td) {
  padding: 12px;
  border: 1px solid #e4e7ed;
}

.markdown-preview :deep(table th) {
  background: #f5f7fa;
  font-weight: 600;
}

.markdown-preview :deep(table tr:hover) {
  background: #fafafa;
}

.markdown-preview :deep(hr) {
  margin: 24px 0;
  border: none;
  border-top: 2px solid #e4e7ed;
}

.step-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.task-learning {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.task-detail h3 {
  font-size: 18px;
  color: #1e293b;
  margin-bottom: 16px;
  border-left: 4px solid #3b82f6;
  padding-left: 12px;
}

.task-description, .task-requirements {
  margin-bottom: 32px;
  background: #f8fafc;
  padding: 20px;
  border-radius: 8px;
}

.submission-area {
  border: 1px solid #e5e7eb;
  padding: 24px;
  border-radius: 8px;
}

.quiz-learning {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 24px 40px;
}

.quiz-container {
  background: #fff;
}

.quiz-item {
  margin-bottom: 32px;
  padding: 24px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.question-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.quiz-option {
  display: block;
  margin-bottom: 12px;
  margin-left: 0 !important;
  padding: 12px;
  border-radius: 6px;
  width: 100%;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.quiz-option:hover {
  background: #fff;
  border-color: #cbd5e1;
}

.quiz-option.is-checked {
  background: #eff6ff;
  border-color: #3b82f6;
}

@media (max-width: 1200px) {
  .learning-layout {
    grid-template-columns: 240px 1fr;
  }
}

.loading-container {
  padding: 40px;
  background: white;
  height: 100vh;
}

/* 固定textarea大小，禁用拖拽 */
.fixed-textarea :deep(textarea) {
  resize: none !important;
  min-height: 240px;
  max-height: 240px;
  overflow-y: auto;
}
</style>