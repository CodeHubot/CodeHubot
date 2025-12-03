<template>
  <div class="string-node-config">
    <el-form-item label="操作类型">
      <el-select v-model="config.operation" style="width: 100%;">
        <el-option label="拼接" value="concat" />
        <el-option label="替换" value="replace" />
        <el-option label="截取" value="substring" />
        <el-option label="格式化" value="format" />
        <el-option label="去空格" value="trim" />
        <el-option label="转大写" value="upper" />
        <el-option label="转小写" value="lower" />
      </el-select>
    </el-form-item>
    <el-form-item label="输入字符串">
      <el-input
        v-model="config.input_string"
        type="textarea"
        :rows="3"
        placeholder="请输入字符串，支持变量替换"
      />
    </el-form-item>
    <el-form-item v-if="config.operation === 'concat'" label="字符串列表">
      <el-input
        v-model="config.operation_params_json"
        type="textarea"
        :rows="3"
        placeholder='["字符串1", "字符串2"]'
      />
    </el-form-item>
    <el-form-item v-if="config.operation === 'concat'" label="分隔符">
      <el-input v-model="config.separator" placeholder="分隔符，默认为空" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'replace'" label="旧文本">
      <el-input v-model="config.old_text" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'replace'" label="新文本">
      <el-input v-model="config.new_text" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'substring'" label="起始位置">
      <el-input-number v-model="config.start" :min="0" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'substring'" label="结束位置">
      <el-input-number v-model="config.end" :min="0" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'format'" label="格式化字符串">
      <el-input v-model="config.format_string" placeholder="例如：Hello {name}" />
    </el-form-item>
    <el-form-item v-if="config.operation === 'format'" label="格式化参数">
      <el-input
        v-model="config.format_args_json"
        type="textarea"
        :rows="3"
        placeholder='{"name": "World"}'
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
  operation: props.node.data?.operation || 'concat',
  input_string: props.node.data?.input_string || '',
  operation_params: props.node.data?.operation_params || {},
  operation_params_json: JSON.stringify(props.node.data?.operation_params || {}, null, 2),
  separator: props.node.data?.operation_params?.separator || '',
  old_text: props.node.data?.operation_params?.old_text || '',
  new_text: props.node.data?.operation_params?.new_text || '',
  start: props.node.data?.operation_params?.start || 0,
  end: props.node.data?.operation_params?.end || 0,
  format_string: props.node.data?.operation_params?.format_string || '',
  format_args: props.node.data?.operation_params?.format_args || {},
  format_args_json: JSON.stringify(props.node.data?.operation_params?.format_args || {}, null, 2)
})

watch(() => config.value.operation_params_json, (newVal) => {
  try {
    const parsed = JSON.parse(newVal)
    if (Array.isArray(parsed)) {
      config.value.operation_params = { strings: parsed, separator: config.value.separator }
    }
    emitUpdate()
  } catch (e) {
    // JSON解析失败，忽略
  }
})

watch(() => config.value.format_args_json, (newVal) => {
  try {
    config.value.format_args = JSON.parse(newVal)
    emitUpdate()
  } catch (e) {
    // JSON解析失败，忽略
  }
})

watch(() => [
  config.value.operation,
  config.value.input_string,
  config.value.separator,
  config.value.old_text,
  config.value.new_text,
  config.value.start,
  config.value.end,
  config.value.format_string
], () => {
  emitUpdate()
}, { deep: true })

const emitUpdate = () => {
  const operationParams = {}
  
  if (config.value.operation === 'concat') {
    operationParams.strings = JSON.parse(config.value.operation_params_json || '[]')
    operationParams.separator = config.value.separator
  } else if (config.value.operation === 'replace') {
    operationParams.old_text = config.value.old_text
    operationParams.new_text = config.value.new_text
  } else if (config.value.operation === 'substring') {
    operationParams.start = config.value.start
    operationParams.end = config.value.end
  } else if (config.value.operation === 'format') {
    operationParams.format_string = config.value.format_string
    operationParams.format_args = config.value.format_args
  }
  
  emit('update', {
    operation: config.value.operation,
    input_string: config.value.input_string,
    operation_params: operationParams
  })
}
</script>

