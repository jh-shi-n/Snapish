<template>
    <div class="max-w-4xl mx-auto bg-white shadow-xl rounded-xl overflow-hidden">
      <main class="pb-20 px-4">
        <!-- Loading state -->
        <div v-if="loading" class="fixed inset-0 flex justify-center items-center bg-white bg-opacity-75 z-50">
          <div class="flex flex-col items-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <span class="text-lg text-blue-600 font-medium">로딩중...</span>
          </div>
        </div>

        <!-- Today's tide section -->
        <section class="mb-2 pt-6">
          <router-link to="/spots"
            class="group flex justify-between items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-xl transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500">
            <h2 class="text-xl font-bold text-blue-800 group-hover:text-blue-900 transition duration-300">오늘의 낚시 스팟</h2>
            <ChevronRightIcon class="w-6 h-6 text-blue-500 group-hover:text-blue-600 transition duration-300" />
          </router-link>
          <div class="mt-4">
            <MulddaeWidget></MulddaeWidget>
          </div>
        </section>

        <!-- My caught fish section -->
        <section v-if="isAuthenticated" class="mb-2 pt-3">
          <router-link to="/catches"
            class="group flex justify-between items-center p-4 bg-green-50 hover:bg-green-100 rounded-xl transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-green-500">
            <h2 class="text-xl font-bold text-green-800 group-hover:text-green-900 transition duration-300">내가 잡은 물고기</h2>
            <ChevronRightIcon class="w-6 h-6 text-green-500 group-hover:text-green-600 transition duration-300" />
          </router-link>
          <div v-if="isLoadingCatches" class="text-center text-gray-500 mt-4">
            <div class="animate-pulse">Loading...</div>
          </div>
          <div v-else-if="displayedCatches.length > 0" 
            ref="scrollContainer"
            class="overflow-x-auto touch-pan-x relative group">
            <div class="flex space-x-2 py-1">
              <div v-for="catchItem in displayedCatches" :key="catchItem.id"
                class="bg-white p-4 rounded-xl shadow-lg flex-shrink-0 w-72 transition-all duration-300 hover:shadow-xl hover:scale-105">
                <img :src="`${BACKEND_BASE_URL}/uploads/${catchItem.imageUrl}`" 
                  alt="Catch Image"
                  class="w-full h-48 object-cover rounded-lg mb-3 cursor-pointer"
                  @click="openImagePopup(catchItem.imageUrl)" />
                <p class="text-gray-800 text-lg font-semibold text-center">
                  {{ catchItem.detections[0].label }}
                </p>
                <p class="text-blue-600 text-sm font-medium text-center mt-1">
                  신뢰도: {{ (catchItem.detections[0].confidence * 100).toFixed(2) }}%
                </p>
              </div>
            </div>
          </div>
          <div v-else class="text-gray-600 text-center p-6 bg-gray-50 rounded-xl mt-4">
            <FishIcon class="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p class="font-medium">아직 잡은 물고기가 없습니다.</p>
            <p class="text-sm mt-1">첫 물고기를 잡아보세요!</p>
          </div>
        </section>

        <!-- Today's hot issues section -->
        <section class="mb-2 pt-3">
          <router-link to="/community"
            class="group flex justify-between items-center p-4 bg-red-50 hover:bg-red-100 rounded-xl transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500">
            <h2 class="text-xl font-bold text-red-800 group-hover:text-red-900 transition duration-300">오늘의 핫이슈</h2>
            <ChevronRightIcon class="w-6 h-6 text-red-500 group-hover:text-red-600 transition duration-300" />
          </router-link>
          <div class="space-y-4 mt-4">
            <router-link v-for="issue in hotIssues" :key="issue.post_id" 
              :to="`/community/${issue.post_id}`" 
              class="block p-4 bg-white rounded-xl shadow-md hover:shadow-lg transition duration-300">
              <div class="flex gap-4">
                <div class="w-24 h-24 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0">
                  <img 
                    :src="getImageUrl(issue.images[0])" 
                    :alt="issue.title"
                    class="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
                    @error="$event.target.src = DEFAULT_IMAGE"
                  />
                </div>
                <div class="flex-1 space-y-2">
                  <h3 class="font-bold text-lg text-gray-800 line-clamp-1 break-all">{{ issue.title }}</h3>
                  <p class="text-sm text-gray-600 line-clamp-2 break-all whitespace-pre-wrap">{{ issue.content }}</p>
                  <div class="flex items-center justify-between text-sm text-gray-500">
                    <span class="font-medium text-blue-600">{{ issue.username }}</span>
                    <div class="flex items-center space-x-1">
                      <Heart class="w-4 h-4 text-red-500" />
                      <span class="font-semibold text-gray-800">{{ issue.likes_count }}</span>
                      <MessageCircle class="w-4 h-4 text-blue-500" />
                      <span class="font-semibold text-gray-800">{{ issue.comments_count }}</span>
                    </div>
                    <span class="flex items-center">
                      <ClockIcon class="w-4 h-4 text-gray-400 mr-1" />
                      <span>{{ new Date(issue.created_at).toLocaleDateString() }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </section>
      </main>
    </div>
  <!-- Image Popup -->
  <div v-if="isImagePopupVisible"
    class="fixed inset-0 bg-black bg-opacity-90 flex justify-center items-center z-50 p-4"
    @click="isImagePopupVisible = false">
    <div class="relative w-full max-w-4xl max-h-[90vh] flex items-center justify-center" @click.stop>
      <div class="relative">
        <img 
          :src="popupImageUrl" 
          alt="Popup Image"
          class="w-auto h-auto max-w-full max-h-[85vh] rounded-lg shadow-xl object-contain"
        />
        <button 
          @click="isImagePopupVisible = false"
          class="absolute top-4 right-4 p-2 bg-white rounded-full hover:bg-gray-100 transition-colors shadow-lg">
          <X class="w-5 h-5 text-gray-600" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ChevronRightIcon,
  ClockIcon,
  X,
  Heart,
  MessageCircle,
  FishIcon,
} from 'lucide-vue-next'
import { onMounted, computed, ref, watch, onUnmounted } from "vue";
import { useStore } from "vuex";
import MulddaeWidget from '../components/MulddaeWidget.vue';
import axios from 'axios';

const store = useStore();
const baseUrl = process.env.VUE_APP_BASE_URL;
const BACKEND_BASE_URL = baseUrl;

const loading = ref(true);
const isLoadingCatches = ref(false);
const isAuthenticated = computed(() => store.getters.isAuthenticated);

const getImageUrl = (url) => {
  if (!url) return DEFAULT_IMAGE;
  return url.startsWith('http') ? url : `${BACKEND_BASE_URL}/uploads/${url}`;
};

onMounted(async () => {
  try {
    loading.value = true;
    await store.dispatch('fetchInitialData');
    if (isAuthenticated.value && catches.value.length > 0) {
      updateDisplayedCatches();
      startAutoSlide();
    }
    const response = await axios.get('/api/posts/top');
    hotIssues.value = response.data;
  } catch (error) {
    console.error('Error:', error);
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  stopAutoSlide();
});

const catches = computed(() => store.getters.catches);
const isImagePopupVisible = ref(false);
const popupImageUrl = ref('');
const displayedCatches = ref([]);

function openImagePopup(imageUrl) {
  popupImageUrl.value = `${BACKEND_BASE_URL}/uploads/${imageUrl}`;
  isImagePopupVisible.value = true;
}

function updateDisplayedCatches() {
  displayedCatches.value = catches.value.slice().reverse();
}

watch(() => catches.value, () => {
  if (catches.value.length > 0) {
    updateDisplayedCatches();
  }
}, { immediate: true });

const autoSlideInterval = ref(null);
const scrollContainer = ref(null);

function startAutoSlide() {
  if (!autoSlideInterval.value) {
    autoSlideInterval.value = setInterval(() => {
      if (scrollContainer.value) {
        const container = scrollContainer.value;
        const scrollAmount = 300;
        if (container.scrollLeft + container.clientWidth >= container.scrollWidth) {
          container.scrollTo({
            left: 0,
            behavior: 'smooth'
          });
        } else {
          container.scrollTo({
            left: container.scrollLeft + scrollAmount,
            behavior: 'smooth'
          });
        }
      }
    }, 3000);
  }
}

function stopAutoSlide() {
  if (autoSlideInterval.value) {
    clearInterval(autoSlideInterval.value);
    autoSlideInterval.value = null;
  }
}

const DEFAULT_IMAGE = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7snbTrr7jsp4Ag7JeG7J2EPC90ZXh0Pjwvc3ZnPg==';

const hotIssues = ref([]);
</script>

<style scoped>
.touch-pan-x {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.touch-pan-x::-webkit-scrollbar {
  display: none;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.break-all {
  word-break: break-all;
  overflow-wrap: break-word;
  white-space: normal;
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}
</style>