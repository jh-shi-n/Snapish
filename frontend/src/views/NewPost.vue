<template>
  <div class="min-h-screen bg-white">
    <main class="h-screen flex flex-col">
      <!-- Top action bar -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <button 
          @click="$router.go(-1)"
          class="p-2 -ml-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100/80 transition-all duration-200"
        >
          <X class="w-6 h-6" />
        </button>
        <div class="flex items-center space-x-3">
          <button
            type="button"
            @click="submitPost"
            :disabled="isSubmitting"
            class="px-4 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
          >
            <Send class="w-4 h-4" />
            <span>{{ isSubmitting ? '작성 중...' : '작성' }}</span>
          </button>
        </div>
      </div>

      <!-- Content area -->
      <div class="flex-1 overflow-y-auto">
        <form @submit.prevent="submitPost" class="h-full">
          <div class="p-4 space-y-6">
            <!-- Title input -->
            <div class="relative">
              <input
                type="text"
                v-model.trim="title"
                required
                :maxlength="maxTitleLength"
                @input="handleTitleInput"
                class="w-full text-2xl font-bold bg-transparent border-0 focus:ring-0 p-0 placeholder-gray-400"
                placeholder="제목을 입력하세요"
              >
              <div class="absolute top-0 right-0 text-sm" :class="isTitleLengthValid ? 'text-gray-400' : 'text-red-500'">
                {{ title.length }}/{{ maxTitleLength }}
              </div>
            </div>

            <!-- Content input -->
            <div class="relative">
              <textarea
                v-model.trim="content"
                required
                rows="8"
                :maxlength="maxContentLength"
                @input="handleContentInput"
                class="w-full text-lg bg-transparent border-0 focus:ring-0 p-0 placeholder-gray-400 resize-none"
                placeholder="내용을 입력하세요"
              ></textarea>
              <div class="absolute bottom-0 right-0 text-sm" :class="isContentLengthValid ? 'text-gray-400' : 'text-red-500'">
                {{ content.length }}/{{ maxContentLength }}
              </div>
            </div>

            <!-- Image upload -->
            <div>
              <div class="relative">
                <!-- Empty state -->
                <div 
                  class="border-2 border-dashed border-gray-200 rounded-2xl hover:border-blue-400 transition-colors duration-200 cursor-pointer"
                  @click="$refs.fileInput.click()"
                >
                  <div class="flex flex-col items-center justify-center py-8">
                    <div class="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
                      <ImagePlus class="w-8 h-8 text-blue-500" />
                    </div>
                    <div class="text-center">
                      <p class="text-sm font-medium text-gray-900 mb-1">이미지를 업로드하세요</p>
                      <p class="text-xs text-gray-500">PNG, JPG, GIF (최대 10MB)</p>
                    </div>
                  </div>
                </div>

                <input
                  ref="fileInput"
                  type="file"
                  class="hidden"
                  accept="image/*"
                  multiple
                  @change="handleImageUpload"
                >
              </div>

              <!-- Image previews -->
              <div v-if="imagePreviews.length > 0" class="mt-4 grid grid-cols-2 gap-4">
                <div 
                  v-for="(preview, index) in imagePreviews" 
                  :key="index"
                  class="relative rounded-2xl overflow-hidden group aspect-video"
                >
                  <img
                    :src="preview"
                    alt="Preview"
                    class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
                  >
                  <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <button
                      type="button"
                      @click="removeImage(index)"
                      class="bg-white/10 backdrop-blur-sm text-white rounded-full p-3 hover:bg-white/20 transform hover:scale-110 transition-all duration-200"
                    >
                      <Trash2 class="w-6 h-6" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </main>
  </div>
</template>

<script>
import axios from '@/axios'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { X, Send, Trash2, ImagePlus } from 'lucide-vue-next'

export default {
  name: 'NewPost',
  components: {
    X,
    Send,
    Trash2,
    ImagePlus
  },
  setup() {
    const router = useRouter()
    const store = useStore()
    const title = ref('')
    const content = ref('')
    const imageFiles = ref([])
    const imagePreviews = ref([])
    const isSubmitting = ref(false)
    const maxContentLength = 500
    const isContentLengthValid = ref(true)
    const maxTitleLength = 50
    const isTitleLengthValid = ref(true)

    const handleImageUpload = (event) => {
      const files = Array.from(event.target.files)
      
      for (const file of files) {
        if (file.size > 10 * 1024 * 1024) {
          alert('각 이미지의 크기는 10MB를 초과할 수 없습니다.')
          continue
        }

        imageFiles.value.push(file)
        const reader = new FileReader()
        reader.onload = (e) => {
          imagePreviews.value.push(e.target.result)
        }
        reader.readAsDataURL(file)
      }
    }

    const removeImage = (index) => {
      imageFiles.value.splice(index, 1)
      imagePreviews.value.splice(index, 1)
    }

    const handleContentInput = (event) => {
      const text = event.target.value
      if (text.length > maxContentLength) {
        content.value = text.slice(0, maxContentLength)
        isContentLengthValid.value = false
      } else {
        isContentLengthValid.value = true
      }
    }

    const handleTitleInput = (event) => {
      const text = event.target.value
      if (text.length > maxTitleLength) {
        title.value = text.slice(0, maxTitleLength)
        isTitleLengthValid.value = false
      } else {
        isTitleLengthValid.value = true
      }
    }

    const submitPost = async () => {
      if (isSubmitting.value) return

      // Check textarea conditions
      if (!isContentLengthValid.value || content.value.length > maxContentLength) {
        alert('내용은 500자를 초과할 수 없습니다.')
        return
      }
      if (!isTitleLengthValid.value || title.value.length > maxTitleLength) {
        alert('제목은 50자를 초과할 수 없습니다.')
        return
      }

      if (!isTitleLengthValid.value || title.value.length <= 0) {
        alert('제목을 작성하셔야합니다.')
        return
      }
      if (!isContentLengthValid.value || content.value.length <= 0) {
        alert('내용을 작성하셔야합니다.')
        return
      }

      isSubmitting.value = true

      try {
        const formData = new FormData()
        formData.append('title', title.value)
        formData.append('content', content.value)
        
        imageFiles.value.forEach(file => {
          formData.append('images', file)
        })

        await axios.post('/api/posts', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${store.state.token}`
          }
        })

        router.push('/community')
      } catch (error) {
        console.error('Error creating post:', error)
        alert('게시물 작성 중 오류가 발생했습니다.')
      } finally {
        isSubmitting.value = false
      }
    }

    return {
      title,
      content,
      imagePreviews,
      isSubmitting,
      handleImageUpload,
      removeImage,
      submitPost,
      maxContentLength,
      isContentLengthValid,
      handleContentInput,
      maxTitleLength,
      isTitleLengthValid,
      handleTitleInput
    }
  }
}
</script>

<style scoped>
/* Smooth image loading */
img {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

img[loading] {
  opacity: 0;
  transform: scale(0.95);
}

img.loaded {
  opacity: 1;
  transform: scale(1);
}

/* Custom scrollbar */
textarea {
  scrollbar-width: thin;
  scrollbar-color: #CBD5E0 #EDF2F7;
  resize: none;
  overflow-y: auto;
  min-height: 200px;
}

textarea::-webkit-scrollbar {
  width: 4px;
}

textarea::-webkit-scrollbar-track {
  background: transparent;
}

textarea::-webkit-scrollbar-thumb {
  background: #CBD5E0;
  border-radius: 2px;
}

textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Remove autofill background */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea:-webkit-autofill,
textarea:-webkit-autofill:hover,
textarea:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0px 1000px white inset;
  transition: background-color 5000s ease-in-out 0s;
}
</style>