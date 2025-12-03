<template>
  <div class="knowledge-node-config">
    <el-form-item label="知识库UUID">
      <el-input
        v-model="config.kb_uuid"
        placeholder="请输入知识库UUID"
      />
    </el-form-item>
    <el-form-item label="查询文本">
      <el-input
        v-model="config.query"
        type="textarea"
        :rows="3"
        placeholder="请输入查询文本，支持变量替换，如：{input.query}"
      />
    </el-form-item>
    <el-form-item label="Top-K">
      <el-input-number
        v-model="config.top_k"
        :min="1"
        :max="20"
      />
    </el-form-item>
    <el-form-item label="相似度阈值">
      <el-input-number
        v-model="config.similarity_threshold"
        :min="0"
        :max="1"
        :step="0.1"
        :precision="2"
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
  kb_uuid: props.node.data?.kb_uuid || '',
  query: props.node.data?.query || '',
  top_k: props.node.data?.top_k || 5,
  similarity_threshold: props.node.data?.similarity_threshold || 0.7
})

watch(config, (newVal) => {
  emit('update', newVal)
}, { deep: true })
</script>

