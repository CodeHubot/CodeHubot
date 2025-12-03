<template>
  <div class="start-node-config">
    <el-alert type="info" :closable="false">
      开始节点无需配置，直接接收工作流输入参数
    </el-alert>
  </div>
</template>

<script setup>
defineProps({
  node: {
    type: Object,
    required: true
  }
})

defineEmits(['update'])
</script>

