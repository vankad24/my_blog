import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomePage.vue'),
  },
  {
    path: '/post/:slug',
    name: 'PostDetail',
    component: () => import('@/views/PostDetail.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterPage.vue'),
  },
  {
    path: '/profile/:login',
    name: 'Profile',
    component: () => import('@/views/ProfilePage.vue'),
  },
  {
    path: '/create',
    name: 'CreatePost',
    component: () => import('@/views/CreatePost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/edit/:slug',
    name: 'EditPost',
    component: () => import('@/views/EditPost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/liked',
    name: 'LikedPosts',
    component: () => import('@/views/LikedPosts.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/moderation',
    name: 'Moderation',
    component: () => import('@/views/ModerationPage.vue'),
    meta: { requiresAuth: true, requiresModerator: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard для авторизации
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresModerator && !authStore.isModerator) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router