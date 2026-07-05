/**
 * 底部导航栏 Tabbar — 数据与导航逻辑
 *
 * 为什么不抽成组件？
 *   快应用组件内 template 的 for 循环 + position: fixed 在某些
 *   平台版本有兼容性问题（实测 Tabbar 组件渲染不出来）。
 *   所以改用「各页面 inline tabbar template + 样式，数据与导航逻辑统一管理」。
 *
 * 用法：
 *   <script>
 *     import { TABS, onTabChange as handleTab } from '../../helper/tabbar'
 *
 *     export default {
 *       private: {
 *         activeTab: 'companion',  // 当前页激活的 tab key
 *         tabs: TABS,
 *       },
 *       onTabChange(key) {
 *         handleTab(this.activeTab, key)
 *       }
 *     }
 *   </script>
 *
 *   <template>
 *     <div class="tabbar">
 *       <div
 *         class="tab-item {{ activeTab === tab.key ? 'tab-active' : '' }}"
 *         for="{{ tabs }}"
 *         onclick="onTabChange({{ tab.key }})"
 *       >
 *         <text class="tab-icon">{{ tab.icon }}</text>
 *         <text class="tab-label">{{ tab.label }}</text>
 *       </div>
 *     </div>
 *   </template>
 */
import router from '@system.router'

/** 4 个 tab 的配置（顺序即展示顺序） */
export const TABS = [
  { key: 'companion', icon: '🏠', label: '陪伴' },
  { key: 'breakIce',  icon: '💬', label: '破冰' },
  { key: 'memory',    icon: '📚', label: '传承' },
  { key: 'profile',   icon: '👤', label: '我的' },
]

/** tab key → 路由路径 */
const ROUTE_MAP = {
  companion: '/pages/Companion',
  breakIce:  '/pages/BreakIce',
  memory:    '/pages/Memory',
  profile:   '/pages/Profile',
}

/**
 * 通用 onTabChange 逻辑
 * @param {string} activeTab 当前页面激活的 tab key
 * @param {string} key 用户点击的 tab key
 */
export function onTabChange(activeTab, key) {
  if (key === activeTab) return
  const uri = ROUTE_MAP[key]
  if (uri) {
    router.replace({ uri })
  }
}