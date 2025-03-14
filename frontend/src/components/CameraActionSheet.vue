<template>
    <!-- 액션 시트 모달 -->
    <div v-if="props.isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-end justify-center z-[100]"
        @click="closeActionSheet">
        <!-- 모달 콘텐츠 -->
        <div class="bg-white w-full max-w-sm rounded-t-xl" @click.stop>
            <div class="p-4">
                <!-- 제목 -->
                <h2 class="text-lg font-semibold text-center mb-4">사진 업로드</h2>
                <div class="space-y-2">
                    <!-- 옵션 버튼들 -->
                    <button v-for="(option, index) in options" :key="index"
                        class="w-full py-3 px-4 text-center text-blue-500 bg-white hover:bg-gray-50 border-b last:border-b-0"
                        @click="handleOption(option.action)">
                        {{ option.text }}
                    </button>
                </div>
                <!-- 취소 버튼 -->
                <button class="w-full py-3 px-4 text-center text-red-500 font-medium mt-2" @click="closeActionSheet">
                    취소
                </button>
            </div>
        </div>
    </div>

    <!-- 숨겨진 파일 입력 요소들 -->
    <input ref="cameraInput" type="file" accept="image/*" capture="environment" style="display: none;"
        @change="onFileChange" />
    <input ref="galleryInput" type="file" accept="image/*" style="display: none;" @change="onFileChange" />
    <input ref="fileInput" type="file" accept="*/*" style="display: none;" @change="onFileChange" />

    <!-- 로딩 오버레이 -->
    <div v-if="isGlobalLoading" class="loading-overlay">
        <img src="/loading_overlay_white.png" alt="Loading" class="floating-image" />
    </div>
</template>

<script setup>
import { ref , computed } from 'vue';
import { useRouter } from 'vue-router';
import store from '../store'; // Vuex store 임포트
import { requestPredict } from '../services/predictService';

// eslint-disable-next-line no-undef
const props = defineProps({
    isOpen: {
        type: Boolean,
        required: true,
    },
});

// eslint-disable-next-line no-undef
const emit = defineEmits(['close']);

// Router 인스턴스
const router = useRouter();

// 파일 입력 요소에 대한 참조 정의
const cameraInput = ref(null);
const galleryInput = ref(null);
const fileInput = ref(null);

// 파일 업로드 용량 제한
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 전역 로딩 상태 가져오기
const isGlobalLoading = computed(() => store.getters.isGlobalLoading);

// 옵션 목록
const options = [
    { text: '사진 촬영', action: 'camera' },
    { text: '갤러리에서 선택', action: 'gallery' },
    { text: '파일 선택', action: 'file' },
];

// 액션 시트를 닫기 위한 함수
const closeActionSheet = () => {
    emit('close');
};

// 옵션 클릭 시 실행되는 함수
const handleOption = (action) => {
    const token = localStorage.getItem("token"); // 토큰 확인
    if (!token) {
        console.log('Login Required');
        alert("로그인이 필요합니다.");
        closeActionSheet();
        router.push("/login");
        return;

    } else {
        console.log('Option selected:', action); // 로그 추가
        closeActionSheet();

        if (action === 'camera') {
            if (cameraInput.value) {
                cameraInput.value.click();
            } else {
                console.error('cameraInput is not available');
            }
        } else if (action === 'gallery') {
            if (galleryInput.value) {
                galleryInput.value.click();
            } else {
                console.error('galleryInput is not available');
            }
        } else if (action === 'file') {
            if (fileInput.value) {
                fileInput.value.click();
            } else {
                console.error('fileInput is not available');
            }
        }
    }

    
};

// 파일 선택 시 실행되는 함수
const onFileChange = async (event) => {
    const file = event.target.files[0];
    if (file) {
        if (file.size > MAX_FILE_SIZE) {
            alert('파일 용량이 너무 큽니다. 10MB 이하의 파일을 선택해주세요.');
            event.target.value = ''; // 파일 입력 초기화
            return;
        }

        try {
            // 전역 로딩 상태 활성화
            store.dispatch('setGlobalLoading', true);

            console.log('before token')
            const token = localStorage.getItem('token');
            if (token) {
                const formData = new FormData();
                formData.append('image', file);
                const response = await requestPredict(formData, token);
                await handlePredictResponse(response);
            } 
        } catch (error) {
            console.error('Error during Axios POST:', error);
            let errorType = null;
            let errorMessage = null;

            console.log(error)

            // 백엔드 에러 응답 처리
            if (error.response?.data) {
                errorType = error.response.data.error
                errorMessage = error.response.data.message
            } else if (error.response === undefined) {
                errorType = 'server_error';
                errorMessage = "서버 접속 실패"
            } else {
                errorType = "analyze_failed"
                errorMessage = "요청 진행 중 실패하였습니다."
            }

            await router.push({
                name: 'FishResultError',
                query: {
                    errorType: errorType,
                    message: errorMessage
                }
            });
        } finally {
            // 전역 로딩 상태 비활성화
            store.dispatch('setGlobalLoading', false);
            // 파일 입력 초기화
            event.target.value = '';
        }
    }
};

const handlePredictResponse = async (data) => {

    // 에러 응답 처리 1 - 서버 연결 실패 시,
    if (data === undefined) {
        await router.push({
            name: 'FishResultError',
            query: {
                errorType: 'server_error',
            }
        });
    }

    // 에러 응답 처리 2 - 
    if (data.status !== '202') {
        console.log('data.errorType:', data.data.error);
        console.log('data.errorType:', data.status);
        await router.push({
            name: 'FishResultError',
            query: {
                errorType: data.status,
                message: data.message,
            }
        });
        return;
    } 

    const detections = data.detections;
    const imageUrl = data.imageUrl || null;
    const imageBase64 = data.image_base64 || null;
    const catchId = data.id || null;
    const assistant_request_id = data.assistant_request_id || null;

    if (detections && detections.length > 0) {
        const currentDate = new Date();
        const currentMonthDay = `${(currentDate.getMonth() + 1).toString().padStart(2, '0')}.${currentDate.getDate().toString().padStart(2, '0')}`;

        console.log('현재 날짜:', currentMonthDay);

        const isProhibited = detections.some(detection => {
            const prohibitedDates = detection.prohibited_dates;
            console.log('감지된 물고기:', detection.label);
            console.log('금어기 날짜:', prohibitedDates);

            if (!prohibitedDates) return false;

            const [start, end] = prohibitedDates.split('~');
            console.log('시작 날짜:', start, '종료 날짜:', end);

            if (end.startsWith('01.')) {
                return (currentMonthDay >= start || currentMonthDay <= end);
            } else {
                return currentMonthDay >= start && currentMonthDay <= end;
            }
        });

        console.log('금어기 여부:', isProhibited);

        const routeName = isProhibited ? 'FishResultWarning' : 'FishResultNormal';
        const queryParams = {
            imageUrl,
            imageBase64,
            detections: encodeURIComponent(JSON.stringify(detections)),
            prohibitedDates: detections[0].prohibited_dates || '알 수 없음',
            timestamp: Date.now(),
            catchId,
            assistant_request_id
        };

        // 현재 경로가 결과 페이지인지 확인
        const isResultPage = router.currentRoute.value.name?.includes('FishResult');
        const navigationMethod = isResultPage ? router.replace : router.push;

        // to-do : apply error status
        if (store.state.isAuthenticated) {
            await store.dispatch('fetchCatches');
            await navigationMethod({
                name: routeName,
                query: {
                    ...queryParams,
                    _timestamp: Date.now()
                }
            });
        } 
    } else {
        alert('알 수 없는 오류가 발생하였습니다.');
    }
};
</script>

<style scoped>
.fixed.inset-0 {
    /* 모달 배경 스타일 */
    display: flex;
    align-items: flex-end;
    justify-content: center;
}

.bg-black.bg-opacity-50 {
    /* 반투명 검은색 배경 */
    background-color: rgba(0, 0, 0, 0.5);
}

.bg-white {
    /* 흰색 배경 */
    background-color: white;
}

.rounded-t-xl {
    /* 모서리 라운딩 */
    border-top-left-radius: 1rem;
    border-top-right-radius: 1rem;
}

.border-b {
    /* 하단 경계선 */
    border-bottom: 1px solid #e5e7eb;
    /* Tailwind gray-200 */
}

.last\:border-b-0 {
    /* 마지막 요소의 하단 경계선 제거 */
    border-bottom: none;
}

.text-blue-500:hover {
    /* 텍스트 및 배경 호버 스타일 */
    color: #3b82f6;
    /* Tailwind의 blue-500 */
    background-color: #f3f4f6;
    /* Tailwind의 gray-100 */
}

.text-red-500 {
    /* 취소 버튼 색상 */
    color: #ef4444;
    /* Tailwind의 red-500 */
}

.space-y-2>*+* {
    /* 버튼 간 간격 */
    margin-top: 0.5rem;
}

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.floating-image {
    width: 300px; /* 원하는 너비로 설정 */
    height: 140px; /* 원하는 높이로 설정 */
    animation: float 2.5s ease-in-out infinite;
}

@keyframes float {
    0% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
    100% {
        transform: translateY(0);
    }
}

</style>