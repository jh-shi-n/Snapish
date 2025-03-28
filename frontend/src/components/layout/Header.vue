<template>
  <header class="bg-white shadow">
    <!-- 네비게이션 바 -->
    <nav class="container mx-auto px-4 py-3 flex justify-between items-center">
      <!-- 사이트 제목 -->
      <h1 class="cursor-pointer" @click="$router.push('/')">
        <img src="/header_snapish.png" alt="SNAPISH" class="h-10 w-50" />
      </h1>
      <div class="flex items-center">
        <button 
          class="p-2" 
          @click="isLoggedIn ? handleLogout() : handleLogin()" 
          :title="isLoggedIn ? '로그아웃' : '로그인'"
        >
          <LogInIcon v-if="!isLoggedIn" class="w-6 h-6" />
          <LogOutIcon v-else class="w-6 h-6" />
        </button>
      </div>
    </nav>
  </header>
</template>

<script>
import { LogInIcon, LogOutIcon } from 'lucide-vue-next'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

export default {
  name: 'AppHeader',
  components: {
    LogInIcon,
    LogOutIcon
  },
  setup() {
    const store = useStore()
    const router = useRouter()

    const isLoggedIn = computed(() => store.getters.isAuthenticated)

    const handleLogout = async () => {
      await store.dispatch('logout')
      router.push('/')
    }

    const handleLogin = () => {
      router.push('/login')
    }

    return {
      isLoggedIn,
      handleLogout,
      handleLogin
    }
  }
}
</script>
