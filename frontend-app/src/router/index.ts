import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import LevelTest from '../views/LevelTest.vue'
import AITutor from '../views/AITutor.vue'
import StudyLog from '../views/StudyLog.vue'
import Settings from '../views/Settings.vue'
const routes = [
  {
    path: '/',     
    name: 'Home',
    component: Home,  
  },
  {
    path: '/level-test', 
    name: 'LevelTest', 
    component: LevelTest
  },
  {
    path: '/aitutor', 
    name: 'AITutor', 
    component: AITutor
  }, 
  {
    path: '/studylog', 
    name: 'StudyLog', 
    component: StudyLog
  }, 
  {
    path: '/settings', 
    name: 'Settings', 
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: routes,
})

export default router
