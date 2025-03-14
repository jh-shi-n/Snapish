<template>
  <div class="min-h-screen bg-white flex flex-col">
    <!-- 헤더 -->
    <header
      class="fixed top-0 left-0 right-0 bg-white px-4 py-3 flex items-center justify-between border-b z-10 max-w-md mx-auto">
      <div class="flex items-center">
        <button class="mr-2" @click="goBack" :disabled="isLoading">
          <ChevronLeftIcon class="w-6 h-6" />
        </button>
        <h1 class="text-xl font-bold">물고기 판별 결과</h1>
      </div>
      <div class="flex items-center">
        <button class="p-2" @click="handleLogout" title="로그아웃">
          <LogOutIcon class="w-6 h-6" />
        </button>
      </div>
    </header>

    <!-- 메인 콘텐츠 -->
    <main class="flex-1 pb-20 px-4 overflow-auto max-w-md mx-auto">
      <!-- 로딩 상태 -->
      <div v-if="loading" class="fixed inset-0 flex justify-center items-center bg-white bg-opacity-75 z-50">
        <div class="flex flex-col items-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
          <span class="text-sm text-gray-500">로딩중...</span>
        </div>
      </div>

      <!-- 에러 메시지 -->
      <div v-if="errorMessage" class="p-4 bg-red-100 text-red-600 rounded-lg">
        {{ errorMessage }}
      </div>

      <!-- 업로드된 물고기 이미지 표시 -->
      <div v-if="!isLoading && !errorMessage" class="mt-4 bg-gray-200 rounded-lg p-4">
        <div class="image-container" :style="imageContainerStyle">
          <div class="image-wrapper">
            <div class="detection-area">
              <img ref="fishImage" :src="imageSource" alt="물고기 사진" :class="imageClass" @click="handleImageClick"
                @load="onImageLoad" />
              <template v-if="imageDimensions.width && imageDimensions.height">
                <div v-for="(detection, index) in parsedDetections" :key="index" class="bounding-box"
                  :style="getBoundingBoxStyle(detection.bbox)">
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 판별 결과 -->
      <div class="mt-6 bg-blue-50 rounded-lg p-4 transition-all duration-300 fade-slide-enter"
           :style="{ transitionDelay: '0ms' }">
        <div class="flex items-center mb-2">
          <h2 class="text-lg font-bold text-blue-700">정상: 현재 포획 가능 어종</h2>
        </div>
        <template v-if="parsedDetections.length > 0">
          <p class="text-blue-600" v-if="parsedDetections[0].label !== '알 수 없음'">
            이 물고기는 <strong>{{ parsedDetections[0].label }}</strong>입니다.
            <span :class="[
              'text-sm',
              getConfidenceColor(parsedDetections[0].confidence)
            ]">
              (신뢰도: {{ (parsedDetections[0].confidence * 100).toFixed(2) }}%)
            </span>
          </p>
          <p class="text-blue-600" v-else>
            이 물고기는 <strong>알 수 없음</strong>으로 판별되었습니다.
          </p>

          <p class="text-sm text-blue-600 mt-2"
            v-if="parsedDetections.length > 1 && parsedDetections[0].label !== '알 수 없음'">
            다른 후보:
            <span class="text-blue-500">
              <span v-for="(detection, index) in parsedDetections.slice(1)" :key="index">
                {{ detection.label }}
                <span :class="[
                  'text-sm',
                  getConfidenceColor(detection.confidence)
                ]">
                  (신뢰도: {{ (detection.confidence * 100).toFixed(2) }}%)
                </span>
                {{ index < parsedDetections.slice(1).length - 1 ? ', ' : '' }} </span>
              </span>
          </p>
        </template>
        <template v-else>
          <p class="text-blue-600">
            예측 결과가 존재하지 않습니다.
          </p>
        </template>
      </div>

      <div v-show="!loading && !errorMessage" 
           class="mt-6 bg-gray-50 rounded-lg p-4 transition-all duration-300 fade-slide-enter"
           :style="{ transitionDelay: '200ms' }">
        <p v-if="isDescriptionLoading" class="text-gray-500 center-align">
          <span class="inline-flex gap-1 center-align">
            정보를 찾아보는 중
            <span class="loading-dots">
              <span>.</span><span>.</span><span>.</span>
            </span>
          </span>
        </p>
        <p v-else>
          <span class="text-gray-700">{{ fishDescription || '설명 없음' }}</span>
          <span class="block text-xs text-gray-700 mt-1">MBRIS 생물종 상세정보 기반 생성형 답변입니다.</span>
        </p>
      </div>

        <!-- AI 모델 경고 문구 추가 -->
        <div v-show="!isLoading && !errorMessage" 
             class="mt-6 mb-4 bg-gray-50 rounded-lg p-3 border border-gray-200 shadow-sm transition-all duration-300 fade-slide-enter"
             :style="{ transitionDelay: '400ms' }">
          <div class="flex flex-col items-center gap-2">
            <div class="flex items-center justify-center gap-2 text-yellow-500">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span class="font-semibold">AI 판별 주의사항</span>
            </div>
            <p class="text-sm text-gray-600 text-center leading-tight">
              인공지능 모델의 판별 결과는 참고용입니다.<br>
              실제 상황과 법적 규제를 반드시 확인하세요.
            </p>
          </div>
        </div>

      <!-- 버튼들 -->
      <div v-show="!isLoading && !errorMessage" 
           class="transition-all duration-300 fade-slide-enter"
           :style="{ transitionDelay: '600ms' }">
        <!-- 공유하기 버튼 -->
        <div class="mt-4">
          <button class="w-full bg-green-500 text-white py-3 px-4 rounded-lg flex items-center justify-center"
            @click="shareResult" :disabled="isLoading">
            <Share2Icon class="w-5 h-5 mr-2" />
            <span>공유하기</span>
          </button>
        </div>

        <!-- 물고기 정보 수정 버튼 -->
        <div v-if="store.state.isAuthenticated" class="mt-4">
          <button class="w-full bg-blue-500 text-white py-3 px-4 rounded-lg flex items-center justify-center"
            @click="openEditModal">
            <Edit class="w-5 h-5 mr-2" />
            <span>물고기 정보 수정</span>
          </button>
        </div>

        <!-- 내가 잡은 물고기 페이지로 이동 버튼 -->
        <div class="mt-4">
          <button class="w-full bg-blue-500 text-white py-3 px-4 rounded-lg flex items-center justify-center"
            @click="navigateToCatches" :disabled="isLoading">
            <InfoIcon class="w-5 h-5 mr-2" />
            <span>내가 잡은 물고기 리스트 보기</span>
          </button>
        </div>
      </div>

      <!-- 추가 로딩 인디케이터 -->
      <div v-if="isLoadingMore" class="flex justify-center items-center py-8">
        <div class="flex flex-col items-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2"></div>
          <span class="text-sm text-gray-500">데이터를 불러오는 중...</span>
        </div>
      </div>
    </main>

    <!-- 포토카드 모달 -->
    <div v-if="showModal && !isLoading"
      class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-[60] max-w-md mx-auto">
      <div class="bg-white rounded-lg shadow-lg p-6 w-10/12 max-w-sm">
        <h2 class="text-lg font-bold mb-4 text-center">나만의 포토카드</h2>
        <div ref="photocard" class="bg-gray-100 p-4 rounded-lg overflow-auto">
          <img :src="imageSource" alt="물고기 사진" class="w-full h-64 object-contain rounded-lg" />
          <h3 class="text-md font-semibold mt-4 text-center">{{ parsedDetections[0].label }}</h3>
          <p class="text-center text-sm">신뢰도: {{ (parsedDetections[0].confidence * 100).toFixed(2) }}%</p>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          <button @click="closeModal" class="px-4 py-2 bg-gray-300 rounded" :disabled="isLoading">닫기</button>
          <button @click="downloadPhotocard" class="px-4 py-2 bg-blue-500 text-white rounded"
            :disabled="isLoading">저장하기</button>
        </div>
      </div>
    </div>

    <!-- 이미지 팝업 -->
    <div v-if="isImagePopupVisible"
      class="fixed inset-0 bg-black bg-opacity-90 flex justify-center items-center z-50 p-4"
      @click="isImagePopupVisible = false">
      <div class="relative w-full max-w-4xl max-h-[90vh] flex items-center justify-center" @click.stop>
        <div class="relative">
          <img :src="popupImageUrl" alt="Popup Image"
            class="w-auto h-auto max-w-full max-h-[85vh] rounded-lg shadow-xl object-contain" />
          <button @click="isImagePopupVisible = false"
            class="absolute top-4 right-4 p-2 bg-white rounded-full hover:bg-gray-100 transition-colors shadow-lg">
            <X class="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>
    </div>

    <!-- Add consent modal -->
    <ConsentModal v-if="showConsentModal" :isVisible="showConsentModal" @close="handleConsentClose"
      @consent="handleConsent" />

    <!-- Add edit fish modal -->
    <EditFishModal v-if="showEditModal" :isVisible="showEditModal" :catchData="selectedCatch"
      @close="showEditModal = false" @save="handleFishDataSave" />
  </div>
</template>

<script setup>
console.log("FishResultNormal script loaded"); // Debugging log

import { ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import html2canvas from 'html2canvas';
import { ChevronLeftIcon, LogOutIcon, Share2Icon, InfoIcon, Edit, X } from 'lucide-vue-next';
import { useStore } from 'vuex';
import { fetchchatgptAssist } from "../services/predictService.js"
import axios from "axios"
import ConsentModal from '../components/ConsentModal.vue';
import EditFishModal from '../components/EditFishModal.vue';

const store = useStore();
const route = useRoute();
const router = useRouter();

const isLoading = ref(true);
const errorMessage = ref('');
const parsedDetections = ref([]);
const imageUrl = ref('');
const imageBase64 = ref('');
const showModal = ref(false);
const photocard = ref(null);
const popupImageUrl = ref('');
const isImagePopupVisible = ref(false);
const fishImage = ref(null);
const imageDimensions = ref({ width: 0, height: 0 });
const showConsentModal = ref(false);
const showEditModal = ref(false);
const selectedCatch = ref(null);
const loading = ref(true);
const isLoadingMore = ref(false);
const isDescriptionLoading = ref(true);

// ChatGPT assistant Get result
const assistant_request_id = computed(() => {
  const assistantIdFromQuery = route.query.assistant_request_id;
  return assistantIdFromQuery || null;
});
const fishDescription = ref('ChatGPT로 생성된 물고기 설명'); // 필요에 따라 물고기 설명을 추가하세요.
// Define backend base URL
const baseUrl = process.env.VUE_APP_BASE_URL;
const BACKEND_BASE_URL = baseUrl;

// Temporary Disable
// const fishName = computed(() => {
//   if (parsedDetections.value.length > 0 && parsedDetections.value[0].label !== '알 수 없음') {
//     return parsedDetections.value[0].label;
//   }
//   return '알 수 없는 물고기';
// });

// ChatGPT Assistant Response 
const fetchAssistantResponse = async (assistantRequestId = null) => {
  // 파라미터가 없으면 null 값 활용
  const currentAssistantId = assistantRequestId || assistant_request_id.value;
  if (!currentAssistantId) 
    return;

  isDescriptionLoading.value = true;
  try {
    const [thread_id, run_id] = currentAssistantId;
    const response = await fetchchatgptAssist(thread_id, run_id);

    if (response) {
      fishDescription.value = response || '생성 중 오류가 발생했어요';
    } else {
      console.error('Error in ChatGPT response:', response.status);
      fishDescription.value = '현재 서비스를 이용할 수 없어요';
    }
  } catch (error) {
    console.error('Error fetching ChatGPT response:', error);
    fishDescription.value = '현재 서비스를 이용할 수 없어요';
  } finally {
    isDescriptionLoading.value = false;
  }
};

// fetchDetections 메서드 수정
const fetchDetections = async () => {
  isLoading.value = true;
  isLoadingMore.value = true;
  try {
    const token = localStorage.getItem('token');
    if (token && route.query.imageUrl) {
      const response = await axios.get(`${baseUrl}/predict/save`, {
        params: {
          imageUrl: route.query.imageUrl,
        },
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      parsedDetections.value = response.data.detections;
      imageUrl.value = response.data.imageUrl;
    } 
    errorMessage.value = '';
  } catch (e) {
    console.error('Failed to fetch detections:', e);
    errorMessage.value = '예측 결과를 불러오는 데 실패했습니다.';
    parsedDetections.value = [];
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
};

onMounted(async () => {
  console.log('컴포넌트가 마운트되었습니다.');

  // 기본 데이터 초기화
  imageUrl.value = route.query.imageUrl || '';
  imageBase64.value = route.query.imageBase64 ? decodeURIComponent(route.query.imageBase64) : '';

  // 실제 이미지 로딩만 loading 상태로 관리
  const img = new Image();
  img.src = imageSource.value;
  img.onload = () => {
    loading.value = false;
  };
  img.onerror = () => {
    loading.value = false;
    if (imageSource.value === '/placeholder.svg') {
      errorMessage.value = '이미지를 불러오는 데 실패했습니다.';
    }
  };

  // ChatGPT 응답은 별도로 실행
  fetchAssistantResponse();

  // 다른 데이터 로딩은 별도로 처리
  try {
    // 디텍션 데이터 가져오기 (loading 상태와 무관)
    await fetchDetections();
    
    // 인증된 사용자인 경우 추가 작업
    if (store.state.isAuthenticated) {
      await store.dispatch('fetchInitialData');
      try {
        const consentStatus = await store.dispatch('checkConsent');
        if (!consentStatus.hasConsent) {
          showConsentModal.value = true;
        }
      } catch (error) {
        console.error('Error checking consent:', error);
      }
    }
  } catch (error) {
    console.error('Error during initialization:', error);
    errorMessage.value = '데이터를 불러오는 데 실패했습니다.';
  }

  // 컴포넌트가 마운트된 후 약간의 지연을 두고 요소들이 보이도록 함
  setTimeout(() => {
    const elements = document.querySelectorAll('.fade-slide-enter');
    elements.forEach(el => {
      el.classList.add('fade-slide-enter-active');
    });
  }, 100);
});

watch(
  () => route.query,
  async (newQuery) => {
    console.log('Route query changed:', newQuery);
    
    // 이미지 관련 데이터 갱신
    imageUrl.value = newQuery.imageUrl || '';
    imageBase64.value = newQuery.imageBase64 ? decodeURIComponent(newQuery.imageBase64) : '';
    
    // detections 갱신
    if (newQuery.detections) {
      parsedDetections.value = JSON.parse(decodeURIComponent(newQuery.detections));
    }

    // ChatGPT 응답 갱신 - 중복 코드 제거
    if (newQuery.assistant_request_id) {
      await fetchAssistantResponse(newQuery.assistant_request_id);
    }

    // 이미지 로딩 처리
    const img = new Image();
    img.src = imageSource.value;
    loading.value = true;
    
    img.onload = () => {
      loading.value = false;
      if (fishImage.value) {
        onImageLoad();
      }
    };
    
    img.onerror = () => {
      loading.value = false;
      if (imageSource.value === '/placeholder.svg') {
        errorMessage.value = '이미지를 불러오는 데 실패했습니다.';
      }
    };
  },
  { deep: true }
);

// 신뢰도에 따른 색상 클래스 반환
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'text-green-600';
  if (confidence >= 0.5) return 'text-yellow-600';
  return 'text-red-600';
};

// 공유하기 기능 구현
const shareResult = () => {
  showModal.value = true;
};

// 포토카드 모달 닫기
const closeModal = () => {
  showModal.value = false;
};

// 포토카드 다운로드
const downloadPhotocard = () => {
  if (photocard.value) {
    html2canvas(photocard.value, { useCORS: true, scale: 2 }).then((canvas) => {
      const link = document.createElement('a');
      link.download = 'photocard.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    });
  }
};

// 이미지 소스 계산
const imageSource = computed(() => {
  if (imageUrl.value && store.state.isAuthenticated) {
    return `${BACKEND_BASE_URL}/uploads/${imageUrl.value}`; // Authenticated users get the image from backend
  } else if (imageBase64.value) {
    return `data:image/jpeg;base64,${imageBase64.value}`; // Unauthenticated users get base64 image
  }
  return '/placeholder.svg'; // Fallback placeholder
});

// 이미지 클릭 핸들러
const handleImageClick = () => {
  if (imageSource.value === '/placeholder.svg') {
    alert('이미지를 불러올 수 없습니다.');
    return;
  }
  openImagePopup(imageSource.value);
};

// 이미지 팝업 열기
function openImagePopup(imageSrc) {
  // Directly assign imageSrc without adding '/uploads/' again
  popupImageUrl.value = imageSrc;
  isImagePopupVisible.value = true;
}

// 내가 잡은 물고기 페이지로 이동
function navigateToCatches() {
  router.push('/catches');
}

// 뒤로 가기 기능 구현
const goBack = () => {
  router.back();
};

const onImageLoad = () => {
  const imageElement = fishImage.value;
  if (imageElement) {
    imageDimensions.value = {
      width: imageElement.naturalWidth,
      height: imageElement.naturalHeight
    };

    // resize 이벤트 리스너 추가
    window.addEventListener('resize', updateBoundingBoxes);
    // 초기 bbox 업데이트를 위해 약간의 지연 추가
    setTimeout(updateBoundingBoxes, 100);
  }
};

const getBoundingBoxStyle = (bbox) => {
  if (!Array.isArray(bbox)) {
    console.warn('Invalid bbox format:', bbox);
    return {};
  }

  const [x1, y1, x2, y2] = bbox;
  const imageElement = fishImage.value;

  if (!imageElement || !imageDimensions.value.width || !imageDimensions.value.height) {
    return {};
  }

  const renderedWidth = imageElement.clientWidth;
  const renderedHeight = imageElement.clientHeight;

  const scaleX = renderedWidth / imageDimensions.value.width;
  const scaleY = renderedHeight / imageDimensions.value.height;

  return {
    left: `${x1 * scaleX}px`,
    top: `${y1 * scaleY}px`,
    width: `${(x2 - x1) * scaleX}px`,
    height: `${(y2 - y1) * scaleY}px`
  };
};

// 이미지 크기에 따른 클래스 계산
const imageClass = computed(() => {
  return 'detection-image';
});

const imageContainerStyle = computed(() => {
  if (!imageDimensions.value.width || !imageDimensions.value.height) {
    return {
      minHeight: 'fit-content',
      padding: '0.5rem'
    };
  }

  const style = {
    minHeight: 'fit-content',
    padding: '0.5rem'
  };

  // 작은 이미지일 경우 패딩 제거
  if (imageDimensions.value.width < 800) {
    style.padding = '0';
  }

  return style;
});

// 컴포넌트 언마운트 시 이벤트 리스너 제거
onUnmounted(() => {
  window.removeEventListener('resize', updateBoundingBoxes);
});

// bbox 업데이트 함수
const updateBoundingBoxes = () => {
  // 강제로 Vue가 bbox를 다시 계산하도록 함
  imageDimensions.value = { ...imageDimensions.value };
};

const handleConsentClose = () => {
  showConsentModal.value = false;
};

const handleConsent = async (consented) => {
  if (!consented) {
    router.push('/');
    return;
  }
};

const handleFishDataSave = async (updatedData) => {
  try {
    await store.dispatch('updateCatch', updatedData);
    showEditModal.value = false;
    router.push('/catches');
  } catch (error) {
    console.error('Error saving fish data:', error);
  }
};

const openEditModal = () => {
  console.log("openEditModal function called"); // Debugging log
  const catchId = route.query.catchId;
  console.log("Route Query:", route.query); // Debugging log
  console.log("Catch ID:", catchId); // Debugging log

  if (catchId) {
    // Fetch the catch data from the store
    const catchData = store.getters.catches.find(c => c.id === parseInt(catchId));
    console.log("Catch Data:", catchData); // Debugging log
    if (catchData) {
      selectedCatch.value = { ...catchData };
      showEditModal.value = true;
    } else {
      console.error('Catch data not found in store'); // Debugging log
      alert('수정할 수 있는 물고기 정보가 없습니다.');
    }
  } else {
    console.error('Catch ID not found in route query'); // Debugging log
    alert('수정할 수 있는 물고기 정보가 없습니다.');
  }
};

const handleLogout = async () => {
  await store.dispatch('logout')
  router.push('/login')
};
</script>

<style scoped>
.image-container {
  position: relative;
  width: 100%;
  background-color: #f3f4f6;
  min-height: fit-content;
  padding: 0.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.detection-area {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  max-width: 100vw;
  /* 화면 너비 최대로 설정 */
}

.detection-image {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  object-fit: contain;
  cursor: pointer;
}

/* 작은 이미지 처리를 위한 스타일 */
.small-image {
  width: 100vw;
  max-width: none;
  margin: -0.5rem;
  /* 컨테이너 패딩 상쇄 */
}

.bounding-box {
  position: absolute;
  border: 2px solid red;
  pointer-events: none;
  background-color: rgba(255, 0, 0, 0.1);
}

.fixed {
  position: fixed;
}

.absolute {
  position: absolute;
}

.object-contain {
  object-fit: contain;
  width: 100%;
  height: 100%;
}

.relative {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f3f4f6;
  min-height: 300px;
}

.absolute.inset-0 {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.aspect-\[4\/3\] {
  aspect-ratio: 4/3;
}

.loading-dots span {
  animation: loadingDots 1.4s infinite;
  opacity: 0;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes loadingDots {
  0% { opacity: 0; transform: translateY(0); }
  25% { opacity: 1; transform: translateY(-4px); }
  50% { opacity: 0; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(0); }
}

.fade-slide-enter {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-enter-active {
  opacity: 1;
  transform: translateY(0);
}

/* 초기 상태에서 요소들을 숨김 */
div[v-show="false"] {
  opacity: 0;
  transform: translateY(20px);
}
</style>
