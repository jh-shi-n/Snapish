<template>
  <div class="min-h-screen bg-gray-100 flex justify-center">
    <div class="w-full max-w-4xl bg-white shadow-lg overflow-hidden parent-container">
      <main class="pb-20 px-4">
        <section class="mb-3 pt-6">
          <div id="top-map">
            <!-- 버튼 추가 -->
            <button @click="toggleMapComponent" 
                    :class="['show-map-btn', { 'close-map-btn': isMapVisible }]">
              {{ isMapVisible ? '닫기' : '전체 위치' }}
            </button>
            <div v-if="isMapVisible && locations.length > 0" class="map-container">
              <MapComponent :locations="locations"></MapComponent>
            </div>
          </div>

          <div id="searchbar">
            <div class="search-filter-container">
              <input v-model="searchQuery" type="text" placeholder="원하는 낚시터 이름을 넣어주세요" key="search-input"
                class="form-control search-input" @input="filterLocations" />
              <div class="filter-container">
                <div class="filter-button" @click="toggleFilterMenu">
                  필터 <span v-if="selectedTypes.length">( {{ selectedTypes.length }} )</span>
                </div>
                <div v-if="showFilterMenu" class="filter-menu">
                  <div v-for="type in locationTypes" :key="type" class="filter-item">
                    <input type="checkbox" 
                      :id="type" 
                      :value="type" 
                      v-model="selectedTypes"
                      @change="filterLocations">
                    <label :for="type">{{ type }}</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        <br />

        <section class="mb-3">
          <div id="middle-list" :style="{
            maxHeight: `${dynamicMaxHeight}px`,
            overflowY: 'scroll',
            paddingRight: '10px'
          }">
            <div>
              <ul class="location-list">
                <li v-for="(location, index) in filteredLocations" :key="index" class="location-item"
                  @click="showDetails(location)">
                  <h3> 
                    <strong :class="['type-tag', `type-${location.type}`]">
                      {{ location.type }}
                    </strong>
                    {{ location.name }} 
                  </h3>
                  <p v-if="location.address_road && location.address_land">
                    {{ location.address_road }}
                  </p>
                  <p v-else-if="location.address_road">
                    {{ location.address_road }}
                  </p>
                  <p v-else-if="location.address_land">
                    {{ location.address_land }}
                  </p>
                </li>
              </ul>
            </div>
          </div>

          <div class="slide-up-panel" 
              :class="{ visible: isDetailsVisible }" 
              @click.self="hideDetails"
              :style="{ overflow: isDetailsVisible ? 'hidden' : 'auto' }">
            <MapLocationDetail 
              v-if="isDetailsVisible" 
              :location="selectedLocation" 
              @close="hideDetails" 
            />
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script>
import axios from "@/axios";
import MapComponent from '@/components/MapComponent.vue'
import MapLocationDetail from '@/components/MapLocationDetail.vue'

export default {
  components: {
    MapComponent,
    MapLocationDetail,
  },
  data() {
    return {
      searchQuery: "", // 검색 입력값
      filteredLocations: [],
      locations: [], // DB에서 위치 데이터를 저장할 배열 - 임시 데이터 넣어둠
      isMapVisible: false, // 지도 표시 여부
      selectedLocation: null, // 선택된 낚시터 데이터
      isDetailsVisible: false, // 상세 정보 슬라이드 표시 여부
      dynamicMaxHeight: window.innerHeight,
      locationTypes: ['바다', '저수지', '평지', '기타'],
      selectedTypes: [],
      showFilterMenu: false,
      filterMenuRef: null, // 필터 메뉴 참조를 위한 속성 추가
    };
  },
  mounted() {
    this.fetchLocations();     // 컴포넌트가 마운트된 후에 DB에서 위치 정보 가져오기
    this.filteredLocations = this.locations; // 초기에는 모든 locations를 표시
    this.updateMaxHeight();     // 페이지 드래그 방지 및 스크롤 숨김 설정
    window.addEventListener("resize", this.updateMaxHeight); // 화면 크기 변화 감지
    window.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.updateMaxHeight); // 이벤트 제거
    window.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    filterLocations() {
      const query = this.searchQuery.trim();
      let filtered = [...this.locations];
      
      // 이름으로 필터링
      if (query !== "") {
        filtered = filtered.filter((location) =>
          String(location.name || "").includes(query)
        );
      }
      
      // 타입으로 필터링
      if (this.selectedTypes.length > 0) {
        filtered = filtered.filter(location => 
          this.selectedTypes.includes(location.type)
        );
      }
      
      this.filteredLocations = filtered;
    },
    updateMaxHeight() {
      const headerHeight = 240;
      const footerHeight = 100;
      const availableHeight = window.innerHeight - headerHeight - footerHeight;
      this.dynamicMaxHeight = Math.max(availableHeight, 300);
    },
    showDetails(location) {
      this.selectedLocation = location;
      this.isDetailsVisible = true;
      document.body.classList.add('detail-active');
    },
    hideDetails() {
      this.selectedLocation = null;
      this.isDetailsVisible = false;
      document.body.classList.remove('detail-active');
    },
    toggleMapComponent() {
      this.isMapVisible = !this.isMapVisible;
    },
    // DB에서 위치 정보 가져오기, 주소 고정값 추후 해결
    async fetchLocations() {
      try {
        const baseUrl = process.env.VUE_APP_BASE_URL; 
        const response = await axios.get(`${baseUrl}/api/spots`);

        if (response.status === 200) {
          this.locations = response.data.data          
          this.filteredLocations = [...this.locations];
        }

      } catch (error) {
        console.error('Error fetching locations:', error);
      }
    },
    toggleFilterMenu(event) {
      event.stopPropagation(); // 이벤트 버블링 방지
      this.showFilterMenu = !this.showFilterMenu;
    },
    handleClickOutside(event) {
      const filterContainer = document.querySelector('.filter-container');
      if (this.showFilterMenu && filterContainer && !filterContainer.contains(event.target)) {
        this.showFilterMenu = false;
      }
    },
  }
};
</script>

<style scoped>
.parent-container {
  position: relative;
  /* 부모 컨테이너 기준점 */
  overflow: hidden;
  /* 부모 밖으로 나가는 요소 숨김 */
}

#top-map {
  display: right;
  /* flex-direction: column; 요소들을 세로로 배치 */
  gap: 5px;
  /* 요소 간격 설정 */
  margin-bottom: 0;
  /* 아래 여백 제거 */
}

#searchbar {
  margin-top: 100px;
}

/* 버튼 스타일 */
.show-map-btn {
  margin: 0;
  padding: 8px 16px;
  background-color: #45a049;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  font-size: 12px;
}

.show-map-btn:hover {
  background-color: #3d8e41;
}

.close-map-btn {
  background-color: #dc3545 !important; /* 빨간색 */
}

.close-map-btn:hover {
  background-color: #c82333 !important;
}

/* 지도 컨테이너 */
.map-container {
  position: absolute;
  top: 75px;
  left: 0;
  width: 100%;
  height: 75%;
  background-color: white;
  z-index: 10;
  /* box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); */
  /* border-bottom: 1px solid #ddd; */
}

/* 리스트 스타일 */
.location-item {
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.slide-up-panel {
  position: absolute; /* absolute에서 fixed로 변경 */
  bottom: 60px;
  left: 0;
  width: 100%;
  height: 90%;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  transform: translateY(100%);
  transition: transform 0.3s ease-in-out;
  z-index: 10; /* z-index 증가 */
  overflow: hidden; /* 패널 자체는 overflow hidden */
}

.slide-up-panel.visible {
  transform: translateY(0);
}

.details-content {
  padding: 20px;
  overflow-y: auto;
  max-height: 100%;
}

/* 검색바 */
#searchbar {
  display: flex;
  align-items: center;
  margin-top: 20px;
  gap: 10px;
}

.search-input {
  flex: 1;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.search-btn {
  padding: 5px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.search-btn:hover {
  background-color: #0056b3;
}

/* body 스크롤 방지를 위한 클래스 */
:global(body.detail-active) {
  overflow: hidden;
}

.search-filter-container {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.filter-container {
  position: relative;
}

.filter-button {
  padding: 8px 16px;
  background-color: #f0f0f0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.filter-button:hover {
  background-color: #e0e0e0;
}

.filter-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 5px;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  z-index: 1000;
}

.filter-item {
  margin: 5px 0;
  white-space: nowrap;
}

.filter-item label {
  margin-left: 5px;
}

.search-input {
  flex: 1;
  min-width: 0;
}

/* 타입 태그 기본 스타일 */
.type-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.9em;
  color: white;
}

/* 각 타입별 배경색 */
.type-바다 {
  background-color: #4AA8D8;
}

.type-저수지 {
  background-color: #98D8A0;
}

.type-평지 {
  background-color: #4CAF50;
}

.type-기타 {
  background-color: #9E9E9E;
}
</style>