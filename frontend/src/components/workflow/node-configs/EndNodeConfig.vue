<template>
  <div class="end-node-config">
    <el-alert type="info" :closable="false">
      结束节点无需配置，自动收集所有节点输出作为工作流结果
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

