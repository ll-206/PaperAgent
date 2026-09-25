<template>
  <div class="flex h-screen overflow-hidden">
    <Content class="flex-grow" />
    <SideBar class="w-80 flex-none" />
  </div>
</template>

<style scoped></style>

<script setup lang="ts">
import Content from './content/ContentView.vue'
import SideBar from './sidebar/SideBar.vue'
// import { useMessageListStore } from '@/stores/messageList'

onMounted(() => {
  console.log('Chat page mounted')
})
</script>
