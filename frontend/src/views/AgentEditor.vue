<template>
  <div class="agent-editor">
    <el-page-header @back="goBack" :content="pageTitle">
      <template #extra>
        <el-button type="primary" @click="saveAgent" :loading="saving">
          <el-icon><Document /></el-icon>
          保存
        </el-button>
      </template>
    </el-page-header>

    <el-card class="editor-card" v-loading="loading">
      <el-tabs v-model="activeTab" class="editor-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form :model="agentForm" :rules="rules" ref="formRef" label-width="120px">
            <el-form-item label="智能体名称" prop="name">
              <el-input v-model="agentForm.name" placeholder="请输入智能体名称" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="agentForm.description"
                type="textarea"
                :rows="3"
                placeholder="请输入智能体描述"
              />
            </el-form-item>
            <el-form-item label="状态" prop="is_active">
              <el-radio-group v-model="agentForm.is_active">
                <el-radio :label="1">激活</el-radio>
                <el-radio :label="0">禁用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 系统提示词 -->
        <el-tab-pane label="系统提示词" name="prompt">
          <div class="prompt-editor">
            <div class="editor-header">
              <span class="header-title">系统提示词配置</span>
              <el-button text @click="showPromptTemplates">
                <el-icon><Document /></el-icon>
                使用模板
              </el-button>
            </div>
            <el-input
              v-model="agentForm.system_prompt"
              type="textarea"
              :rows="20"
              placeholder="请输入系统提示词，用于指导 AI 智能体的行为和角色定位

示例：
你是一个专业的物联网助手，擅长帮助用户管理和控制智能设备。
你的主要职责包括：
1. 解答用户关于设备使用的问题
2. 帮助用户控制智能设备（如开关灯、调节温度等）
3. 分析传感器数据并提供建议
4. 设置自动化场景

请用友好、专业的语气与用户交流。"
              class="prompt-textarea"
            />
            <div class="prompt-tips">
              <el-alert
                title="提示"
                type="info"
                :closable="false"
                show-icon
              >
                <ul>
                  <li>系统提示词用于定义智能体的角色、能力和行为规范</li>
                  <li>清晰的提示词能让智能体更好地理解用户需求</li>
                  <li>建议包含：角色定位、主要功能、交互风格等</li>
                </ul>
              </el-alert>
            </div>
          </div>
        </el-tab-pane>

        <!-- 插件配置 -->
        <el-tab-pane label="插件配置" name="plugins">
          <div class="plugins-config">
            <div class="plugins-header">
              <span class="header-title">已关联插件 ({{ agentForm.plugin_ids.length }})</span>
              <el-button type="primary" @click="showPluginSelector">
                <el-icon><Plus /></el-icon>
                添加插件
              </el-button>
            </div>

            <el-empty v-if="selectedPlugins.length === 0" description="暂未关联任何插件">
              <el-button type="primary" @click="showPluginSelector">添加插件</el-button>
            </el-empty>

            <div v-else class="plugins-list">
              <el-card
                v-for="plugin in selectedPlugins"
                :key="plugin.id"
                class="plugin-card"
                shadow="hover"
              >
                <template #header>
                  <div class="plugin-card-header">
                    <span class="plugin-name">{{ plugin.name }}</span>
                    <el-button
                      type="danger"
                      size="small"
                      text
                      @click="removePlugin(plugin.id)"
                    >
                      <el-icon><Delete /></el-icon>
                      移除
                    </el-button>
                  </div>
                </template>
                <div class="plugin-description">{{ plugin.description || '暂无描述' }}</div>
                <div class="plugin-meta">
                  <el-tag size="small">{{ plugin.plugin_type }}</el-tag>
                  <el-tag size="small" :type="plugin.is_active ? 'success' : 'info'">
                    {{ plugin.is_active ? '激活' : '禁用' }}
                  </el-tag>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 插件选择对话框 -->
    <el-dialog
      v-model="pluginSelectorVisible"
      title="选择插件"
      width="800px"
    >
      <el-input
        v-model="pluginSearchQuery"
        placeholder="搜索插件名称"
        clearable
        style="margin-bottom: 20px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-table
        :data="filteredPlugins"
        @selection-change="handlePluginSelectionChange"
        max-height="400px"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="插件名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="plugin_type" label="类型" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="scope">
            <el-tag size="small" :type="scope.row.is_active ? 'success' : 'info'">
              {{ scope.row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="pluginSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPluginSelection">确定</el-button>
      </template>
    </el-dialog>

    <!-- 提示词模板对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      title="选择提示词模板"
      width="700px"
    >
      <div class="template-list">
        <el-card
          v-for="template in promptTemplates"
          :key="template.id"
          class="template-card"
          shadow="hover"
          @click="useTemplate(template)"
        >
          <div class="template-name">{{ template.name }}</div>
          <div class="template-desc">{{ template.description }}</div>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Delete, Search } from '@element-plus/icons-vue'
import { getAgent, updateAgent } from '@/api/agent'
import { getPlugins } from '@/api/plugin'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const activeTab = ref('basic')
const formRef = ref(null)
const pluginSelectorVisible = ref(false)
const templateDialogVisible = ref(false)
const pluginSearchQuery = ref('')
const availablePlugins = ref([])
const selectedPluginIds = ref([])

const agentId = computed(() => parseInt(route.params.id))
const pageTitle = computed(() => agentForm.name || '智能体编排')

const agentForm = reactive({
  id: null,
  name: '',
  description: '',
  system_prompt: '',
  plugin_ids: [],
  is_active: 1
})

const rules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 提示词模板
const promptTemplates = [
  {
    id: 1,
    name: '物联网设备助手',
    description: '专业的物联网设备管理和控制助手',
    content: `你是一个专业的物联网助手，擅长帮助用户管理和控制智能设备。

你的主要职责包括：
1. 解答用户关于设备使用的问题
2. 帮助用户控制智能设备（如开关灯、调节温度等）
3. 分析传感器数据并提供建议
4. 设置自动化场景

请用友好、专业的语气与用户交流，并在必要时主动询问以获取更多信息。`
  },
  {
    id: 2,
    name: '数据分析助手',
    description: '专注于传感器数据分析和可视化',
    content: `你是一个数据分析专家，专注于物联网传感器数据的分析和解读。

你的核心能力：
1. 分析温度、湿度等传感器数据的趋势
2. 发现数据中的异常情况并告警
3. 提供数据可视化建议
4. 基于历史数据做出预测

请用专业但易懂的方式解释数据，帮助用户做出明智的决策。`
  },
  {
    id: 3,
    name: '智能家居管家',
    description: '贴心的智能家居生活助手',
    content: `你是一个贴心的智能家居管家，致力于让用户的生活更舒适便捷。

你的服务内容：
1. 根据用户习惯自动调节家居环境
2. 提供节能建议
3. 设置场景模式（如回家模式、睡眠模式）
4. 提醒维护和保养设备

请以管家的身份，用亲切、体贴的语气与用户交流。`
  },
  {
    id: 4,
    name: '教学助手',
    description: '用于物联网教学的互动助手',
    content: `你是一个物联网教学助手，帮助学生学习物联网知识和实践。

你的教学目标：
1. 讲解物联网基础概念（传感器、通信协议等）
2. 指导学生完成实验项目
3. 解答编程和硬件相关问题
4. 提供项目创意和改进建议

请用耐心、鼓励的方式引导学生学习，注重培养动手能力和创新思维。`
  }
]

// 已选中的插件详情
const selectedPlugins = computed(() => {
  return availablePlugins.value.filter(plugin => 
    agentForm.plugin_ids.includes(plugin.id)
  )
})

// 筛选后的插件列表
const filteredPlugins = computed(() => {
  if (!pluginSearchQuery.value) {
    return availablePlugins.value
  }
  const query = pluginSearchQuery.value.toLowerCase()
  return availablePlugins.value.filter(plugin =>
    plugin.name.toLowerCase().includes(query) ||
    (plugin.description && plugin.description.toLowerCase().includes(query))
  )
})

// 返回上一页
const goBack = () => {
  router.push('/agents')
}

// 加载智能体详情
const loadAgent = async () => {
  if (!agentId.value) return
  
  loading.value = true
  try {
    const response = await getAgent(agentId.value)
    const agent = response.data
    Object.assign(agentForm, {
      id: agent.id,
      name: agent.name,
      description: agent.description,
      system_prompt: agent.system_prompt || '',
      plugin_ids: agent.plugin_ids || [],
      is_active: agent.is_active
    })
  } catch (error) {
    ElMessage.error('加载智能体信息失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载可用插件
const loadPlugins = async () => {
  try {
    const response = await getPlugins({ limit: 9999 })
    availablePlugins.value = response.data.items
  } catch (error) {
    ElMessage.error('加载插件列表失败')
    console.error(error)
  }
}

// 保存智能体
const saveAgent = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请检查基本信息是否填写正确')
    activeTab.value = 'basic'
    return
  }
  
  saving.value = true
  try {
    await updateAgent(agentId.value, agentForm)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 显示插件选择器
const showPluginSelector = () => {
  pluginSearchQuery.value = ''
  selectedPluginIds.value = [...agentForm.plugin_ids]
  pluginSelectorVisible.value = true
}

// 处理插件选择变化
const handlePluginSelectionChange = (selection) => {
  selectedPluginIds.value = selection.map(item => item.id)
}

// 确认插件选择
const confirmPluginSelection = () => {
  agentForm.plugin_ids = [...selectedPluginIds.value]
  pluginSelectorVisible.value = false
  ElMessage.success('插件配置已更新')
}

// 移除插件
const removePlugin = (pluginId) => {
  ElMessageBox.confirm('确定要移除此插件吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    agentForm.plugin_ids = agentForm.plugin_ids.filter(id => id !== pluginId)
    ElMessage.success('插件已移除')
  }).catch(() => {})
}

// 显示提示词模板
const showPromptTemplates = () => {
  templateDialogVisible.value = true
}

// 使用模板
const useTemplate = (template) => {
  ElMessageBox.confirm(
    '使用模板将覆盖当前的系统提示词，是否继续？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    agentForm.system_prompt = template.content
    templateDialogVisible.value = false
    ElMessage.success('模板已应用')
  }).catch(() => {})
}

onMounted(() => {
  loadAgent()
  loadPlugins()
})
</script>

<style scoped>
.agent-editor {
  padding: 20px;
}

.editor-card {
  margin-top: 20px;
  min-height: 600px;
}

.editor-tabs {
  min-height: 500px;
}

.prompt-editor {
  padding: 20px 0;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.prompt-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.6;
}

.prompt-tips {
  margin-top: 20px;
}

.prompt-tips ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.prompt-tips li {
  margin: 5px 0;
}

.plugins-config {
  padding: 20px 0;
}

.plugins-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.plugins-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.plugin-card {
  cursor: default;
}

.plugin-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plugin-name {
  font-weight: 500;
  font-size: 15px;
}

.plugin-description {
  margin-bottom: 10px;
  color: #606266;
  font-size: 13px;
}

.plugin-meta {
  display: flex;
  gap: 8px;
}

.template-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-2px);
  border-color: #409eff;
}

.template-name {
  font-weight: 500;
  font-size: 15px;
  margin-bottom: 8px;
  color: #303133;
}

.template-desc {
  font-size: 13px;
  color: #909399;
}
</style>

