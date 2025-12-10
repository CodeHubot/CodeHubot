<template>
  <div class="markdown-viewer">
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-button-group size="small">
          <el-button 
            :type="viewMode === 'preview' ? 'primary' : ''"
            @click="viewMode = 'preview'"
          >
            <el-icon><View /></el-icon>
            预览
          </el-button>
          <el-button 
            :type="viewMode === 'raw' ? 'primary' : ''"
            @click="viewMode = 'raw'"
          >
            <el-icon><Document /></el-icon>
            原始
          </el-button>
        </el-button-group>
      </div>
      
      <div class="toolbar-right">
        <el-tooltip content="复制原始内容" placement="top">
          <el-button size="small" @click="copyRawContent">
            <el-icon><DocumentCopy /></el-icon>
            复制
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <div class="viewer-content" :class="viewMode">
      <!-- Markdown 预览模式 -->
      <div 
        v-if="viewMode === 'preview'" 
        class="markdown-body"
        v-html="renderedMarkdown"
      />
      
      <!-- 原始文本模式 -->
      <pre v-else class="raw-content">{{ content }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Document, DocumentCopy } from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  defaultMode: {
    type: String,
    default: 'preview', // 'preview' 或 'raw'
    validator: (value) => ['preview', 'raw'].includes(value)
  }
})

const viewMode = ref(props.defaultMode)

// 配置 marked
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true, // 启用 GitHub Flavored Markdown
  headerIds: true,
  mangle: false
})

// 渲染 Markdown
const renderedMarkdown = computed(() => {
  if (!props.content) return ''
  try {
    return marked.parse(props.content)
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return `<pre>${props.content}</pre>`
  }
})

// 复制原始内容
const copyRawContent = async () => {
  try {
    await navigator.clipboard.writeText(props.content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    // 降级方案：使用传统的复制方法
    const textarea = document.createElement('textarea')
    textarea.value = props.content
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    
    try {
      document.execCommand('copy')
      ElMessage.success('已复制到剪贴板')
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
    }
    
    document.body.removeChild(textarea)
  }
}
</script>

<style scoped>
.markdown-viewer {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background: #fff;
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.viewer-content {
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.viewer-content.preview {
  background: #fff;
}

.viewer-content.raw {
  background: #fafafa;
  padding: 0;
}

.raw-content {
  margin: 0;
  padding: 16px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

/* Markdown 样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  word-wrap: break-word;
}

.markdown-body :deep(h1) {
  font-size: 28px;
  font-weight: 600;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaecef;
}

.markdown-body :deep(h2) {
  font-size: 24px;
  font-weight: 600;
  margin: 20px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #eaecef;
}

.markdown-body :deep(h3) {
  font-size: 20px;
  font-weight: 600;
  margin: 16px 0 8px;
}

.markdown-body :deep(h4) {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 6px;
}

.markdown-body :deep(h5) {
  font-size: 14px;
  font-weight: 600;
  margin: 10px 0 6px;
}

.markdown-body :deep(h6) {
  font-size: 13px;
  font-weight: 600;
  margin: 8px 0 4px;
  color: #606266;
}

.markdown-body :deep(p) {
  margin: 8px 0;
  line-height: 1.8;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(blockquote) {
  margin: 16px 0;
  padding: 8px 16px;
  border-left: 4px solid #409eff;
  background: #ecf5ff;
  color: #606266;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  margin: 0 2px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  color: #e83e8c;
}

.markdown-body :deep(pre) {
  margin: 12px 0;
  padding: 16px;
  background: #282c34;
  border-radius: 4px;
  overflow-x: auto;
  line-height: 1.6;
}

.markdown-body :deep(pre code) {
  padding: 0;
  margin: 0;
  background: transparent;
  border: none;
  color: #abb2bf;
  font-size: 13px;
}

.markdown-body :deep(table) {
  margin: 16px 0;
  border-collapse: collapse;
  width: 100%;
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
}

.markdown-body :deep(table th) {
  background: #f5f7fa;
  font-weight: 600;
  text-align: left;
}

.markdown-body :deep(table tr:nth-child(even)) {
  background: #fafafa;
}

.markdown-body :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}

.markdown-body :deep(hr) {
  margin: 24px 0;
  border: none;
  border-top: 1px solid #eaecef;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(del) {
  text-decoration: line-through;
}

/* 滚动条样式 */
.viewer-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.viewer-content::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 4px;
}

.viewer-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
}

.viewer-content::-webkit-scrollbar-thumb:hover {
  background: #a8abb2;
}
</style>

