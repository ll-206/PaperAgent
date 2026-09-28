<template>
  <div id="home" class="app-shell flex min-h-screen">
    <SideBar
      :is-collapsed="isCollapsed"
      @toggle-collapse="isCollapsed = !isCollapsed"
    />
    <router-view class="flex-grow" />
  </div>
</template>

<script setup lang="ts">
const isCollapsed = ref(false)
</script>

<style lang="less" scoped>
.app-shell { background: #f7f9ff; }
@media (max-width: 560px) {
  .app-shell { padding-bottom: 68px; }
}
</style>
