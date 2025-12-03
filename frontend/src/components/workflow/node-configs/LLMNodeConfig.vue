<template>
  <div class="llm-node-config">
    <el-form-item label="智能体UUID">
      <el-input
        v-model="config.agent_uuid"
        placeholder="请输入智能体UUID"
      />
    </el-form-item>
    <el-form-item label="提示词">
      <el-input
        v-model="config.prompt"
        type="textarea"
        :rows="4"
        placeholder="请输入提示词，支持变量替换，如：{input.query}"
      />
      <div class="help-text">支持变量：{input.param}、{node_id}、{node_id.field}</div>
    </el-form-item>
    <el-form-item label="温度">
      <el-input-number
        v-model="config.temperature"
        :min="0"
        :max="2"
        :step="0.1"
        :precision="2"
      />
    </el-form-item>
    <el-form-item label="最大Token">
      <el-input-number
        v-model="config.max_tokens"
        :min="1"
        :max="8192"
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
  agent_uuid: props.node.data?.agent_uuid || '',
  prompt: props.node.data?.prompt || '',
  temperature: props.node.data?.temperature || 0.7,
  max_tokens: props.node.data?.max_tokens || 4096,
  timeout: props.node.data?.timeout || 60
})

watch(config, (newVal) => {
  emit('update', newVal)
}, { deep: true })
</script>

<style scoped>
.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>

