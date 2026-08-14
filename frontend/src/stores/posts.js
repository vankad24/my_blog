import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export const usePostsStore = defineStore('posts', () => {
  const posts = ref([])
  const currentPost = ref(null)
  const tags = ref([])
  const pagination = ref({
    count: 0,
    next: null,
    previous: null,
  })

  async function fetchPosts(params = {}) {
    const { data } = await apiClient.get('/posts/', { params })
    posts.value = data.results || data
    pagination.value = {
      count: data.count || 0,
      next: data.next,
      previous: data.previous,
    }
    return data
  }

  async function fetchPost(slug) {
    const { data } = await apiClient.get(`/posts/${slug}/`)
    currentPost.value = data
    return data
  }

  async function createPost(postData) {
    const { data } = await apiClient.post('/posts/', postData)
    return data
  }

  async function updatePost(slug, postData) {
    const { data } = await apiClient.put(`/posts/${slug}/`, postData)
    currentPost.value = data
    return data
  }

  async function deletePost(slug) {
    await apiClient.delete(`/posts/${slug}/`)
  }

  async function likePost(slug) {
    const { data } = await apiClient.post(`/posts/${slug}/like/`)
    return data
  }

  async function fetchLikedPosts() {
    const { data } = await apiClient.get('/posts/liked/')
    return data.results || data
  }

  async function fetchTags() {
    const { data } = await apiClient.get('/tags/')
    tags.value = data.results || data
    return tags.value
  }

  async function fetchComments(postSlug) {
    const { data } = await apiClient.get('/comments/', {
      params: { content_type: 'posts.post', object_id: postSlug },
    })
    return data.results || data
  }

  async function createComment(commentData) {
    const { data } = await apiClient.post('/comments/', commentData)
    return data
  }

  return {
    posts,
    currentPost,
    tags,
    pagination,
    fetchPosts,
    fetchPost,
    createPost,
    updatePost,
    deletePost,
    likePost,
    fetchLikedPosts,
    fetchTags,
    fetchComments,
    createComment,
  }
})