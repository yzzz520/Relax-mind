<!-- 应用根组件：只承载路由出口，各页面自行管理布局。 -->
<template>
  <div class="app-root">
    <RouterView />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100dvh;
  background: var(--bg-base);
}
</style>
