<template>
  <nav class="navbar">
    <div class="navbar-container">
      <div class="title">
        <RouterLink to="/overview">價格追蹤小幫手</RouterLink>
      </div>
      <div class="hamburger" :class="{ rotated: isMenuOpen }" @click="isMenuOpen = !isMenuOpen">
        <div class="hamburger-line"></div>
        <div class="hamburger-line"></div>
      </div>
    </div>
    <div class="options" :class="{ active: isMenuOpen, 'enable-transition': enableTransition }">
      <div v-for="(option, index) in navigationOptions" :key="option.key" class="option-item"
        @click="isMenuOpen = false" :style="{ '--delay': `${index * 0.1}s` }">
        <RouterLink v-if="option.type === 'link'" :to="option.to">
          {{ option.text }}
        </RouterLink>
        <span v-else-if="option.type === 'action'" @click="option.action">
          {{ option.text }}
        </span>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth";
import { ref, computed, onMounted, onUnmounted } from "vue";

const isMenuOpen = ref(false);
const enableTransition = ref(true);
const userStore = useAuthStore();

const navigationOptions = computed(() => {
  const baseOptions = [
    { key: "overview", type: "link", to: "/overview", text: "物價概覽" },
    { key: "trending", type: "link", to: "/trending", text: "物價趨勢" },
    { key: "news", type: "link", to: "/news", text: "相關新聞" },
  ];

  if (userStore.isLoggedIn) {
    baseOptions.push({
      key: "logout",
      type: "action",
      text: `Hi, ${userStore.getUserName}! 登出`,
      action: () => userStore.logout(),
    });
  } else {
    baseOptions.push({
      key: "login",
      type: "link",
      to: "/login",
      text: "登入",
    });
  }

  return baseOptions;
});

onMounted(() => {
  // 使用 matchMedia 精確監聽斷點變化
  const mediaQuery = window.matchMedia("(max-width: 768px)");

  const handleBreakpointChange = () => {
    enableTransition.value = false;

    if (!mediaQuery.matches) {
      isMenuOpen.value = false;
    }

    setTimeout(() => {
      enableTransition.value = true;
    }, 50);
  };

  mediaQuery.addEventListener("change", handleBreakpointChange);

  onUnmounted(() => {
    mediaQuery.removeEventListener("change", handleBreakpointChange);
  });
});
</script>

<style scoped>
/* 主要導航欄樣式 - 使用 Grid 佈局 */
.navbar {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  width: 100%;
  min-height: 4.5em;
  padding: 1.5em;
  background-color: #f3f3f3;
  box-shadow: 0 0 5px #000000;
}

/* 桌面版 - 單行佈局 */
@media (min-width: 769px) {
  .navbar {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto;
  }
}

/* Navbar 容器 */
.navbar-container {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 1rem;
}

/* 標題樣式 */
.title {
  justify-self: start;
}

.title>a {
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50 !important;
  text-decoration: none;
}

/* 選項列表樣式 - 使用 Grid 佈局 */
.options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem;
  align-items: center;
  justify-items: center;
  grid-column: 1 / -1;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transform: translateY(-10px);
  /* 不在基礎樣式設定 transition，避免媒體查詢切換時動畫 */
}

/* 桌面版 - 顯示選項列表，與標題同行 */
@media (min-width: 769px) {
  .options {
    display: flex;
    flex-direction: row;
    justify-content: flex-end;
    align-items: center;
    gap: 1rem;
    max-height: 100px;
    opacity: 1;
    transform: translateY(0);
    margin-top: 0;
    padding: 0;
    border-top: none;
    grid-column: 2;
    grid-row: 1;
  }
}

/* 選項列表展開狀態 - 只在手機版需要動畫 */
.options.active {
  max-height: 200px;
  opacity: 1;
  transform: translateY(0);
  margin-top: 1rem;
  padding: 1rem;
  border-top: 1px solid #ddd;
}

/* 選項項目樣式 */
.option-item {
  color: #575b5d;
  font-size: 1.2em;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
}

/* 桌面版選項項目樣式 */
@media (min-width: 769px) {
  .option-item {
    font-size: 1.1em;
    padding: 0.4rem 0.8rem;
    white-space: nowrap;
  }
}

.option-item:hover {
  background-color: rgba(44, 62, 80, 0.1);
}

.navbar a {
  text-decoration: none;
  color: inherit;
  display: block;
  width: 100%;
  height: 100%;
}

/* 漢堡選單樣式 */
.hamburger {
  display: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: transform 0.3s ease;
}

.hamburger:hover {
  background-color: rgba(44, 62, 80, 0.1);
}

.hamburger.rotated {
  transform: rotate(90deg);
}

.hamburger-line {
  width: 20px;
  height: 2px;
  background-color: #575b5d;
  margin: 5px 0;
  border-radius: 1px;
}

/* 平板 (768px - 1024px) */
@media (max-width: 1024px) {
  .options {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 0.25rem;
  }

  .option-item {
    font-size: 1.1em;
    padding: 0.4rem 0.8rem;
  }
}

/* 手機 (小於768px) */
@media (max-width: 768px) {

  /* 重新配置 Grid 佈局 */
  .navbar {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
    min-height: auto;
  }

  /* 顯示漢堡選單 */
  .hamburger {
    display: block;
  }

  /* 選項列表 - 垂直佈局，預設隱藏 */
  .options {
    grid-template-columns: 1fr;
    gap: 0.5rem;
    justify-items: stretch;
    max-height: 0;
    opacity: 0;
    transform: translateY(-20px);
    margin-top: 0;
    padding: 0;
    border-top: none;
    /* 預設不啟用動畫 */
    transition: none;
  }

  /* 只在啟用動畫時才添加 transition */
  .options.enable-transition {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* 選項列表展開 */
  .options.active {
    max-height: 400px;
    opacity: 1;
    transform: translateY(0);
    margin-top: 1rem;
    padding: 1rem;
    border-top: 1px solid #ddd;
  }

  /* 選項項目 */
  .option-item {
    font-size: 1.3em;
    padding: 0.8rem 1rem;
    text-align: center;
    border-radius: 8px;
    background-color: rgba(255, 255, 255, 0.5);
  }

  .option-item:hover {
    background-color: rgba(44, 62, 80, 0.1);
  }
}

/* 超小螢幕 (小於480px) */
@media (max-width: 480px) {
  .navbar {
    padding: 1rem;
  }

  .title>a {
    font-size: 1.2em;
  }

  .option-item {
    font-size: 1.1em;
    padding: 0.6rem 0.8rem;
  }
}
</style>
