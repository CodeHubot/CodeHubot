<template>
  <div class="intent-node-config">
    <el-form-item label="输入文本">
      <el-input
        v-model="config.input_text"
        type="textarea"
        :rows="3"
        placeholder="请输入输入文本，支持变量替换"
      />
    </el-form-item>
    <el-form-item label="识别方式">
      <el-select v-model="config.recognition_mode" style="width: 100%;">
        <el-option label="LLM识别" value="llm" />
        <el-option label="关键词匹配" value="keyword" />
      </el-select>
    </el-form-item>
    <el-form-item v-if="config.recognition_mode === 'llm'" label="智能体UUID">
      <el-input
        v-model="config.agent_uuid"
        placeholder="请输入智能体UUID"
      />
    </el-form-item>
    <el-form-item label="意图类别">
      <el-input
        v-model="config.intent_categories_json"
        type="textarea"
        :rows="3"
        placeholder='["查询天气", "播放音乐", "控制设备"]'
      />
    </el-form-item>
    <el-form-item v-if="config.recognition_mode === 'keyword'" label="关键词映射">
      <el-input
        v-model="config.keyword_mapping_json"
        type="textarea"
        :rows="4"
        placeholder='{"查询天气": ["天气", "温度"], "播放音乐": ["音乐", "播放"]}'
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
  input_text: props.node.data?.input_text || '',
  recognition_mode: props.node.data?.recognition_mode || 'llm',
  agent_uuid: props.node.data?.agent_uuid || '',
  intent_categories: props.node.data?.intent_categories || [],
  intent_categories_json: JSON.stringify(props.node.data?.intent_categories || [], null, 2),
  keyword_mapping: props.node.data?.keyword_mapping || {},
  keyword_mapping_json: JSON.stringify(props.node.data?.keyword_mapping || {}, null, 2)
})

watch(() => config.value.intent_categories_json, (newVal) => {
  try {
    config.value.intent_categories = JSON.parse(newVal)
    emit('update', {
      input_text: config.value.input_text,
      recognition_mode: config.value.recognition_mode,
      agent_uuid: config.value.agent_uuid,
      intent_categories: config.value.intent_categories,
      keyword_mapping: config.value.keyword_mapping
    })
  } catch (e) {
    // JSON解析失败，忽略
  }
})

watch(() => config.value.keyword_mapping_json, (newVal) => {
  try {
    config.value.keyword_mapping = JSON.parse(newVal)
    emit('update', {
      input_text: config.value.input_text,
      recognition_mode: config.value.recognition_mode,
      agent_uuid: config.value.agent_uuid,
      intent_categories: config.value.intent_categories,
      keyword_mapping: config.value.keyword_mapping
    })
  } catch (e) {
    // JSON解析失败，忽略
  }
})

watch(() => [config.value.input_text, config.value.recognition_mode, config.value.agent_uuid], () => {
  emit('update', {
    input_text: config.value.input_text,
    recognition_mode: config.value.recognition_mode,
    agent_uuid: config.value.agent_uuid,
    intent_categories: config.value.intent_categories,
    keyword_mapping: config.value.keyword_mapping
  })
}, { deep: true })
</script>

