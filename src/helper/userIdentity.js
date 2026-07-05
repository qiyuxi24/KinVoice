/**
 * 用户身份管理 —— 账号密码登录体系
 *
 * 设计：
 * - 登录后后端返回 user_id（UUID），前端存储到 localStorage
 * - 昵称同时缓存，无需每次请求
 * - 所有 API 请求通过 ajax.js 自动注入 X-User-Id Header
 *
 * 使用方式：
 *   import userIdentity from '../../helper/userIdentity'
 *   await userIdentity.login(username, password)
 *   const userId = userIdentity.getUserId()
 */
import storage from '@system.storage'
import authAPI from './apis/auth'

const KEYS = {
  USER_ID: 'kinvoice_user_id',
  NICKNAME: 'kinvoice_nickname',
}

export default {
  _cachedUserId: null,
  _cachedNickname: null,

  // ==================== 读取本地缓存 ====================

  /**
   * 初始化：从本地存储恢复登录态
   * @returns {Promise<{user_id: string, nickname: string}|null>}
   */
  init() {
    return new Promise((resolve) => {
      let userId = null
      let nickname = null

      const checkDone = () => {
        if (userId !== null && nickname !== null) {
          // 两次异步都完成了
          this._cachedUserId = userId || null
          this._cachedNickname = nickname || ''
          if (userId) {
            resolve({ user_id: userId, nickname: nickname || '' })
          } else {
            resolve(null)
          }
        }
      }

      storage.get({
        key: KEYS.USER_ID,
        success: (data) => {
          userId = data || null
          checkDone()
        },
        fail: () => {
          userId = null
          checkDone()
        },
      })

      storage.get({
        key: KEYS.NICKNAME,
        success: (data) => {
          nickname = data || ''
          checkDone()
        },
        fail: () => {
          nickname = ''
          checkDone()
        },
      })
    })
  },

  // ==================== 独立初始化（供 Family/BreakIce/ChatRoom 等页面使用） ====================

  /**
   * 从本地存储读取 user_id 并缓存。
   * 与 init() 不同：不等待 nickname，适合只需要 user_id 的场景。
   * @returns {Promise<string|null>}
   */
  initUserId() {
    return new Promise((resolve) => {
      storage.get({
        key: KEYS.USER_ID,
        success: (data) => {
          this._cachedUserId = data || null
          resolve(this._cachedUserId)
        },
        fail: () => {
          this._cachedUserId = null
          resolve(null)
        },
      })
    })
  },

  /**
   * 从本地存储读取 nickname 并缓存。
   * @returns {Promise<string>}
   */
  initNickname() {
    return new Promise((resolve) => {
      storage.get({
        key: KEYS.NICKNAME,
        success: (data) => {
          this._cachedNickname = data || ''
          resolve(this._cachedNickname)
        },
        fail: () => {
          this._cachedNickname = ''
          resolve('')
        },
      })
    })
  },

  /** 设置昵称（同时更新缓存 + 持久化到本地存储） */
  setNickname(nickname) {
    this._cachedNickname = nickname || ''
    storage.set({ key: KEYS.NICKNAME, value: this._cachedNickname })
  },

  // ==================== 同步读取 ====================

  /** 获取当前 user_id（未登录返回 null） */
  getUserId() {
    return this._cachedUserId || null
  },

  /** 获取当前昵称 */
  getNickname() {
    return this._cachedNickname || ''
  },

  /** 是否已登录 */
  isLoggedIn() {
    return !!this._cachedUserId
  },

  // ==================== 登录/注册/登出 ====================

  /**
   * 登录
   * @returns {Promise<{user_id, nickname}>}
   */
  async login(username, password) {
    const res = await authAPI.login(username, password)
    this._saveAuth(res.user_id, res.nickname)
    return { user_id: res.user_id, nickname: res.nickname }
  },

  /**
   * 注册
   * @returns {Promise<{user_id, nickname}>}
   */
  async register(username, password, nickname) {
    const res = await authAPI.register(username, password, nickname)
    this._saveAuth(res.user_id, res.nickname)
    return { user_id: res.user_id, nickname: res.nickname }
  },

  /** 登出 */
  logout() {
    this._cachedUserId = null
    this._cachedNickname = null
    storage.delete({ key: KEYS.USER_ID })
    storage.delete({ key: KEYS.NICKNAME })
  },

  // ==================== 内部方法 ====================

  _saveAuth(userId, nickname) {
    this._cachedUserId = userId
    this._cachedNickname = nickname || ''
    storage.set({ key: KEYS.USER_ID, value: userId })
    storage.set({ key: KEYS.NICKNAME, value: this._cachedNickname })
  },
}
