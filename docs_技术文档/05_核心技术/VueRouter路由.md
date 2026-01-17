# Vue Router 路由管理详解

## 概述

Vue Router 是 Vue.js 官方的路由管理器。本文档详细介绍 Vue Router 4 在 CodeHubot 项目中的使用，适合教学和实际开发。

## 基础概念

### 1. 什么是前端路由？

```
传统多页应用:
  /login    → login.html
  /home     → home.html
  /devices  → devices.html
  (每次跳转都刷新页面)

单页应用 (SPA):
  /login    → LoginComponent
  /home     → HomeComponent
  /devices  → DevicesComponent
  (页面不刷新，组件切换)
```

### 2. 安装和配置

```bash
npm install vue-router@4
```

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')  // 懒加载
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

```javascript
// main.js
import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

createApp(App)
  .use(router)
  .mount('#app')
```

## 路由配置

### 1. 基础路由

```javascript
const routes = [
  // 简单路由
  {
    path: '/home',
    component: Home
  },
  
  // 动态路由参数
  {
    path: '/device/:id',
    component: DeviceDetail
  },
  
  // 多个参数
  {
    path: '/course/:courseId/unit/:unitId',
    component: UnitDetail
  },
  
  // 可选参数
  {
    path: '/users/:userId?',  // userId 可选
    component: UserList
  }
]
```

### 2. 嵌套路由

```javascript
{
  path: '/device',
  component: DeviceLayout,
  children: [
    {
      path: '',  // /device
      component: DeviceList
    },
    {
      path: ':id',  // /device/123
      component: DeviceDetail
    },
    {
      path: ':id/control',  // /device/123/control
      component: DeviceControl
    }
  ]
}
```

```vue
<!-- DeviceLayout.vue -->
<template>
  <div>
    <el-header>设备管理</el-header>
    <!-- 子路由组件渲染在这里 -->
    <router-view />
  </div>
</template>
```

### 3. 命名路由和命名视图

```javascript
// 命名路由
{
  path: '/device/:id',
  name: 'DeviceDetail',
  component: DeviceDetail
}

// 命名视图
{
  path: '/dashboard',
  components: {
    default: Dashboard,
    sidebar: Sidebar,
    header: Header
  }
}
```

## 导航

### 1. 声明式导航

```vue
<template>
  <!-- 字符串路径 -->
  <router-link to="/home">首页</router-link>
  
  <!-- 对象形式 -->
  <router-link :to="{ path: '/home' }">首页</router-link>
  
  <!-- 命名路由 -->
  <router-link :to="{ name: 'DeviceDetail', params: { id: 123 } }">
    设备详情
  </router-link>
  
  <!-- 带查询参数 -->
  <router-link :to="{ path: '/devices', query: { page: 1 } }">
    设备列表
  </router-link>
</template>
```

### 2. 编程式导航

```javascript
import { useRouter } from 'vue-router'

const router = useRouter()

// 字符串路径
router.push('/home')

// 对象形式
router.push({ path: '/home' })

// 命名路由
router.push({ 
  name: 'DeviceDetail', 
  params: { id: 123 } 
})

// 带查询参数
router.push({ 
  path: '/devices', 
  query: { page: 1, size: 20 } 
})

// 前进/后退
router.go(-1)  // 后退一步
router.go(1)   // 前进一步
router.back()  // 后退
```

## 路由守卫

### 1. 全局前置守卫

```javascript
// router/index.js
router.beforeEach((to, from, next) => {
  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      // 未登录，跳转到登录页
      next({ 
        path: '/login',
        query: { redirect: to.fullPath }  // 保存目标路由
      })
    } else {
      next()  // 已登录，继续
    }
  } else {
    next()  // 不需要登录，直接通过
  }
})
```

### 2. 全局后置钩子

```javascript
router.afterEach((to, from) => {
  // 设置页面标题
  document.title = to.meta.title || 'CodeHubot'
  
  // 页面滚动到顶部
  window.scrollTo(0, 0)
})
```

### 3. 路由独享守卫

```javascript
{
  path: '/admin',
  component: Admin,
  beforeEnter: (to, from, next) => {
    const user = store.state.user
    if (user.role === 'admin') {
      next()
    } else {
      next('/403')  // 无权限
    }
  }
}
```

### 4. 组件内守卫

```vue
<script setup>
import { onBeforeRouteEnter, onBeforeRouteLeave } from 'vue-router'

// 进入路由前
onBeforeRouteEnter((to, from) => {
  // 在渲染该组件的对应路由被验证前调用
})

// 离开路由前
onBeforeRouteLeave((to, from) => {
  // 离开路由前确认
  const answer = window.confirm('确定要离开吗？未保存的数据将丢失。')
  return answer
})
</script>
```

## CodeHubot 项目实践

### 1. 路由结构

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 导入各模块路由
import aiRoutes from './ai'
import deviceRoutes from './device'

const routes = [
  {
    path: '/',
    name: 'Portal',
    component: () => import('@/views/Portal.vue'),
    meta: { title: '门户' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  
  // AI 模块
  ...aiRoutes,
  
  // 设备模块
  ...deviceRoutes,
  
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 白名单
  const whitelist = ['/login', '/']
  
  if (whitelist.includes(to.path)) {
    next()
  } else if (!authStore.isAuthenticated) {
    // 未登录
    next(`/login?redirect=${to.fullPath}`)
  } else if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
    // 无权限
    next('/403')
  } else {
    next()
  }
})

export default router
```

### 2. 模块路由示例

```javascript
// router/device.js
import DeviceLayout from '@/layouts/DeviceLayout.vue'

export default [
  {
    path: '/device',
    component: DeviceLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'DeviceList',
        component: () => import('@device/views/DeviceList.vue'),
        meta: { 
          title: '设备列表',
          roles: ['admin', 'teacher', 'student']
        }
      },
      {
        path: ':id',
        name: 'DeviceDetail',
        component: () => import('@device/views/DeviceDetail.vue'),
        meta: { 
          title: '设备详情',
          roles: ['admin', 'teacher', 'student']
        }
      },
      {
        path: ':id/control',
        name: 'DeviceControl',
        component: () => import('@device/views/DeviceControl.vue'),
        meta: { 
          title: '设备控制',
          roles: ['admin', 'teacher']  // 学生不可控制
        }
      }
    ]
  }
]
```

### 3. 获取路由参数

```vue
<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 获取路径参数
const deviceId = route.params.id

// 获取查询参数
const page = route.query.page || 1

// 监听路由变化
watch(() => route.params.id, (newId) => {
  console.log('设备ID变化:', newId)
  fetchDeviceDetail(newId)
})
</script>
```

## 高级特性

### 1. 路由元信息

```javascript
{
  path: '/admin',
  component: Admin,
  meta: {
    requiresAuth: true,
    roles: ['admin'],
    title: '管理后台',
    icon: 'Setting',
    keepAlive: true  // 缓存组件
  }
}
```

### 2. 路由懒加载

```javascript
// ✅ 懒加载（推荐）
{
  path: '/device',
  component: () => import('@/views/Device.vue')
}

// ❌ 直接导入
import Device from '@/views/Device.vue'
{
  path: '/device',
  component: Device
}
```

### 3. 路由过渡动画

```vue
<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
```

### 4. 滚动行为

```javascript
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      // 浏览器后退时，恢复滚动位置
      return savedPosition
    } else if (to.hash) {
      // 锚点跳转
      return { el: to.hash, behavior: 'smooth' }
    } else {
      // 默认滚动到顶部
      return { top: 0 }
    }
  }
})
```

## 最佳实践

### 1. 路由懒加载 + 代码分割

```javascript
// ✅ 按模块分割
component: () => import(/* webpackChunkName: "device" */ '@/views/Device.vue')

// ✅ 使用 Vite 的动态导入
component: () => import('@/views/Device.vue')
```

### 2. 路由权限封装

```javascript
// utils/permission.js
export function hasPermission(route, userRole) {
  if (route.meta && route.meta.roles) {
    return route.meta.roles.includes(userRole)
  }
  return true
}
```

### 3. 面包屑导航

```vue
<template>
  <el-breadcrumb>
    <el-breadcrumb-item 
      v-for="item in breadcrumbs"
      :key="item.path"
      :to="item.path"
    >
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const breadcrumbs = computed(() => {
  return route.matched.map(r => ({
    path: r.path,
    title: r.meta.title || r.name
  }))
})
</script>
```

## 教学要点总结

### 核心概念
1. **路由配置**: routes 数组
2. **导航方式**: router-link / router.push
3. **路由参数**: params / query
4. **路由守卫**: beforeEach / afterEach
5. **嵌套路由**: children

### 实用技巧
- ✅ 路由懒加载
- ✅ 路由守卫权限控制
- ✅ 动态路由参数
- ✅ 命名路由
- ✅ 路由元信息

### 最佳实践
- ✅ 模块化路由配置
- ✅ 统一的路由守卫
- ✅ 懒加载优化性能
- ✅ 合理的路由嵌套
- ✅ 清晰的路由命名

## 相关文档

- [前端架构](../02_系统架构/前端架构.md) - 前端架构设计
- [Pinia状态管理](./Pinia状态管理.md) - 状态管理
- [权限管理体系](../01_认证授权/权限管理体系.md) - 权限控制
