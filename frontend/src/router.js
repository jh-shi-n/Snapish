import { createRouter, createWebHistory } from "vue-router";
import store from "./store"; // 스토어 임포트

// 컴포넌트 임포트
import Home from "./views/Home.vue";
import Community from "./views/Community.vue";
import NewPost from "./views/NewPost.vue";
import EditPost from "./views/EditPost.vue";
import FishingSpotLocationService from "./views/FishingSpotLocationService.vue";
import Profile from "./views/Profile.vue";
import FishResultNormal from "./views/FishResultNormal.vue";
import FishResultWarning from "./views/FishResultWarning.vue";
import FishResultError from "./views/FishResultError.vue";
import Login from "./views/Login.vue";
import EditProfile from "./views/EditProfile.vue"; // 프로필 수정 컴포넌트 임포트
import Signup from "./views/Signup.vue"; // Signup 컴포넌트 임포트
import Catches from "./views/Catches.vue"; // Catches 컴포넌트 임포트

// Example for axios base URL configuration
import axios from "axios";

const baseUrl = process.env.VUE_APP_BASE_URL;
axios.defaults.baseURL = baseUrl;

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home, // 홈 컴포넌트
  },
  {
    path: "/community",
    name: "Community",
    component: Community, // 커뮤니티 컴포넌트
    meta: { requiresAuth: true },
  },
  {
    path: "/community/:id", // Dynamic route for individual posts
    name: "CommunityPost",
    component: Community, // You might want to create a separate component for individual posts
    meta: { requiresAuth: true },
  },
  {
    path: "/community/new",
    name: "NewPost",
    component: NewPost,
    meta: { requiresAuth: true },
  },
  {
    path: "/community/edit/:id",
    name: "EditPost",
    component: EditPost,
    meta: { requiresAuth: true },
  },
  {
    path: "/spots",
    name: "FishingSpotLocationService",
    component: FishingSpotLocationService, // 날씨 상세 정보 컴포넌트
  },
  {
    path: "/profile",
    name: "Profile",
    component: Profile, // 프로필 컴포넌트
    meta: { requiresAuth: true }, // 인증이 필요한 라우트로 설정
  },
  {
    path: "/fish-result-normal",
    name: "FishResultNormal",
    component: FishResultNormal,
  },
  {
    path: "/fish-result-warning",
    name: "FishResultWarning",
    component: FishResultWarning, // 물고기 경고 컴포넌트
  },
  {
    path: "/fish-result-error",
    name: "FishResultError",
    component: FishResultError, // 물고기 경고 컴포넌트
  },
  {
    path: "/login",
    name: "Login",
    component: Login, // 로그인 컴포넌트 추가
  },
  {
    path: "/signup",
    name: "Signup",
    component: Signup, // 회원가입 컴포넌트 추가
  },
  {
    path: "/edit-profile",
    name: "EditProfile",
    component: EditProfile, // 프로필 수정 컴포넌트 추가
    meta: { requiresAuth: true },
  },
  {
    path: "/catches",
    name: "Catches",
    component: Catches, // Catches 컴포넌트 추가
    meta: { requiresAuth: true },
  },
];

// 라우터 생성
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    // 항상 페이지 상단으로 스크롤
    return { top: 0 }
  }
});

// 네비게이션 가드 설정 (인증 여부 확인)
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const isAuthenticated = store.getters.isAuthenticated;

  if (requiresAuth && !isAuthenticated) {
    // 토큰이 있을 경우 스토어에 사용자 정보 로드 시도
    if (localStorage.getItem("token")) {
      try {
        await store.dispatch("fetchUserProfile");
        next();
      } catch (error) {
        console.error("Error fetching user profile:", error);
        next("/login");
      }
    } else {
      next("/login");
    }
  } else {
    // 인증된 경우 또는 인증이 필요 없는 라우트
    next(); // 라우팅 진행
  }
});

// 라우트 이동 후 스크롤 상태 관리
router.afterEach((to) => {
  // `FishingSpotLocationService` 라우트로 이동한 경우 스크롤 비활성화
  if (to.name === 'FishingSpotLocationService') {
    document.body.style.overflow = 'hidden';
  } else {
    // 다른 라우트로 이동한 경우 스크롤 초기화
    document.body.style.overflow = 'auto';

    // 혹시 Detail 컴포넌트 DOM 잔여물이 있다면 제거
    const detailComponent = document.querySelector('.fixed.inset-0');
    if (detailComponent) {
      detailComponent.remove(); // DOM에서 제거
    }
  }
});

// 전역 에러 핸들러 추가
router.onError((error) => {
  console.error("Router error:", error);
});

export default router;
