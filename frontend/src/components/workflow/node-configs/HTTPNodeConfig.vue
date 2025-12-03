<template>
  <div class="http-node-config">
    <el-form-item label="URL">
      <el-input
        v-model="config.url"
        placeholder="https://api.example.com/endpoint"
      />
      <div class="help-text">支持变量替换，如：{input.url}</div>
    </el-form-item>
    <el-form-item label="请求方法">
      <el-select v-model="config.method" style="width: 100%;">
        <el-option label="GET" value="GET" />
        <el-option label="POST" value="POST" />
        <el-option label="PUT" value="PUT" />
        <el-option label="DELETE" value="DELETE" />
        <el-option label="PATCH" value="PATCH" />
      </el-select>
    </el-form-item>
    <el-form-item label="请求头">
      <el-input
        v-model="config.headersJson"
        type="textarea"
        :rows="3"
        placeholder='{"Content-Type": "application/json"}'
      />
    </el-form-item>
    <el-form-item label="请求体">
      <el-input
        v-model="config.bodyJson"
        type="textarea"
        :rows="4"
        placeholder='{"key": "value"} 或普通文本'
      />
    </el-form-item>
    <el-form-item label="超时时间(秒)">
      <el-input-number
        v-model="config.timeout"
        :min="1"
        :max="300"
      />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update'])

const config = ref({
  url: props.node.data?.url || '',
  method: props.node.data?.method || 'GET',
  headers: props.node.data?.headers || {},
  headersJson: JSON.stringify(props.node.data?.headers || {}, null, 2),
  body: props.node.data?.body || null,
  bodyJson: props.node.data?.body ? (typeof props.node.data.body === 'string' ? props.node.data.body : JSON.stringify(props.node.data.body, null, 2)) : '',
  timeout: props.node.data?.timeout || 10
})

watch(() => config.value.headersJson, (newVal) => {
  try {
    config.value.headers = JSON.parse(newVal)
    emit('update', {
      url: config.value.url,
      method: config.value.method,
      headers: config.value.headers,
      body: config.value.body,
      timeout: config.value.timeout
    })
  } catch (e) {
    // JSON解析失败，忽略
  }
})

watch(() => config.value.bodyJson, (newVal) => {
  try {
    config.value.body = JSON.parse(newVal)
  } catch (e) {
    config.value.body = newVal
  }
  emit('update', {
    url: config.value.url,
    method: config.value.method,
    headers: config.value.headers,
    body: config.value.body,
    timeout: config.value.timeout
  })
})

watch(() => [config.value.url, config.value.method, config.value.timeout], () => {
  emit('update', {
    url: config.value.url,
    method: config.value.method,
    headers: config.value.headers,
    body: config.value.body,
    timeout: config.value.timeout
  })
}, { deep: true })
</script>

<style scoped>
.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>

