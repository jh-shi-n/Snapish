<template>
  <div class="rounded-xl p-8 shadow-lg overflow-hidden relative">
    <!-- Refresh button -->
    <button 
      class="absolute top-3 right-3 bg-white text-600 rounded-full p-2 shadow-md hover:bg-blue-50 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
      @click="refreshCard"
      title="새로고침"
    >
      <RefreshCcwIcon class="w-5 h-5" />
    </button>
    
    <div class="container">
      <div v-if="loading" class="loading">
        <LoaderIcon class="animate-spin w-8 h-8 text-blue-600 mb-2" />
        <span class="text-blue-600 font-medium">정보를 가져오는 중...</span>
      </div>
      <div v-else-if="mulddae" class="content">
        <div class="left-panel">
          <span class="moon-icon" :title="getMoonPhaseTitle(mulddae.moon_phase)">{{ getMoonIcon(mulddae.moon_phase) }}</span>
        </div>
        <div class="right-panel">
          <div class="date-info">
            <h2 class="text-2xl font-bold text-gray-800">{{ currentDate }}</h2>
            <h3 class="text-lg text-gray-600">음력 {{ mulddae.lunar_date }}</h3>
          </div>
          <div class="mulddae-info mt-2">
            <h3 class="text-xl font-semibold text-blue-800">{{ mulddae.other }}</h3>
            <p class="text-lg text-blue-600">서해 : {{ mulddae.seohae }}</p>
          </div>
        </div>
      </div>
      <div v-else-if="error" class="error text-red-600 font-medium">{{ error }}</div>
      <div v-else class="no-data text-gray-600 font-medium">물때 정보를 불러오지 못했습니다.</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useStore } from 'vuex'
import { RefreshCcwIcon, LoaderIcon } from 'lucide-vue-next'

const store = useStore()

const currentlocation = ref({ lat: 0, lng: 0 }); // 초기값 설정

const moonPhaseIcons = {
  "new": "🌑",
  "waxing_crescent": "🌒",
  "first_quarter": "🌓",
  "waxing_gibbous": "🌔",
  "full": "🌕",
  "waning_gibbous": "🌖",
  "last_quarter": "🌗",
  "waning_crescent": "🌘"
}

const moonPhaseTitles = {
  "new": "신월",
  "waxing_crescent": "초승달",
  "first_quarter": "상현달",
  "waxing_gibbous": "차가는 달",
  "full": "보름달",
  "waning_gibbous": "기우는 달",
  "last_quarter": "하현달",
  "waning_crescent": "그믐달"
}

const loading = computed(() => store.state.loading)
const error = computed(() => store.state.error)
const mulddae = computed(() => store.state.mulddae)

const currentDate = computed(() => {
  return new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\. /g, '-').replace('.', '')
})

const getMoonIcon = (phase) => {
  if (phase === 0) return moonPhaseIcons["new"]
  if (phase > 0 && phase < 0.25) return moonPhaseIcons["waxing_crescent"]
  if (phase === 0.25) return moonPhaseIcons["first_quarter"]
  if (phase > 0.25 && phase < 0.5) return moonPhaseIcons["waxing_gibbous"]
  if (phase === 0.5) return moonPhaseIcons["full"]
  if (phase > 0.5 && phase < 0.75) return moonPhaseIcons["waning_gibbous"]
  if (phase === 0.75) return moonPhaseIcons["last_quarter"]
  if (phase > 0.75 && phase < 1) return moonPhaseIcons["waning_crescent"]
  return "❓"
}

const getMoonPhaseTitle = (phase) => {
  if (phase === 0) return moonPhaseTitles["new"]
  if (phase > 0 && phase < 0.25) return moonPhaseTitles["waxing_crescent"]
  if (phase === 0.25) return moonPhaseTitles["first_quarter"]
  if (phase > 0.25 && phase < 0.5) return moonPhaseTitles["waxing_gibbous"]
  if (phase === 0.5) return moonPhaseTitles["full"]
  if (phase > 0.5 && phase < 0.75) return moonPhaseTitles["waning_gibbous"]
  if (phase === 0.75) return moonPhaseTitles["last_quarter"]
  if (phase > 0.75 && phase < 1) return moonPhaseTitles["waning_crescent"]
  return "알 수 없음"
}

const refreshCard = async () => {
  try {
    console.log("Refresh Mulddae Widget: Cached mulddae data cleared.")
    localStorage.removeItem("mulddae")
    localStorage.removeItem("mulddaeDate")
    await store.dispatch("fetchMulddaeInfo")
  } catch (error) {
    console.error("Error refreshing mulddae data:", error)
  }
}

function updateLocation() {
  // 현재 위치를 업데이트하는 로직
  currentlocation.value = { lat: 0, lng: 0 }; // 예시 값
}

onMounted(() => {
  updateLocation()
})
</script>

<style scoped>
.container {
  @apply flex flex-col items-center justify-center h-full;
}

.loading, .error, .no-data {
  @apply text-lg text-center;
}

.content {
  @apply flex w-full max-w-md gap-8;
}

.left-panel {
  @apply flex items-center justify-center flex-shrink-0;
}

.right-panel {
  @apply flex flex-col justify-between flex-grow;
}

.moon-icon {
  @apply text-8xl;
}

.date-info {
  @apply text-center mb-4;
}

.mulddae-info {
  @apply text-center mt-2;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.content {
  animation: fadeIn 0.5s ease-out;
}
</style>

