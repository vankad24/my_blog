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

  async function fetchPost(id) {
    const { data } = await apiClient.get(`/posts/${id}/`)
    currentPost.value = data
    return data
  }

  async function createPost(postData) {
    const { data } = await apiClient.post('/posts/', postData)
    return data
  }

  async function updatePost(id, postData) {
    const { data } = await apiClient.put(`/posts/${id}/`, postData)
    currentPost.value = data
    return data
  }

  async function deletePost(id) {
    await apiClient.delete(`/posts/${id}/`)
  }

  async function likePost(id) {
    const { data } = await apiClient.post(`/posts/${id}/like/`)
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

  async function fetchComments(postId) {
    const { data } = await apiClient.get('/comments/', {
      params: { content_type: 'posts.post', object_id: postId },
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