/**
<<<<<<< HEAD
 * 用户身份管理 —— 设备 UUID + 昵称
 *
 * 设计：
 * - 每个设备生成唯一 UUID 存 localStorage，作为 user_id
 * - 昵称由用户首次输入，后端注册后缓存到 localStorage
 * - 所有 API 请求通过 Header X-User-Id 传递用户身份
 *
 * 使用方式：
 *   import userIdentity from '../../helper/userIdentity'
 *   const userId = userIdentity.getUserId()
 *   const nickname = userIdentity.getNickname()
 */

import storage from '@system.storage'
=======
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
>>>>>>> si

const KEYS = {
  USER_ID: 'kinvoice_user_id',
  NICKNAME: 'kinvoice_nickname',
}

<<<<<<< HEAD
/**
 * 生成 UUID v4（简化版，快应用兼容）
 */
function generateUUID() {
  const hex = '0123456789abcdef'
  let uuid = ''
  for (let i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      uuid += '-'
    } else if (i === 14) {
      uuid += '4'
    } else if (i === 19) {
      uuid += hex[(Math.random() * 4) | 8]
    } else {
      uuid += hex[(Math.random() * 16) | 0]
    }
  }
  return uuid
}

export default {
  /**
   * 获取或生成用户 ID（同步返回，首次调用时异步初始化）
   * @returns {string} UUID
   */
  getUserId() {
    // 同步读取（storage.get 是异步的，但我们可以缓存）
    if (this._cachedUserId) return this._cachedUserId

    // 首次调用，异步读取并缓存
    storage.get({
      key: KEYS.USER_ID,
      success: (data) => {
        this._cachedUserId = data
      },
      fail: () => {
        // 不存在则生成新 UUID 并存储
        const uuid = generateUUID()
        this._cachedUserId = uuid
        storage.set({
          key: KEYS.USER_ID,
          value: uuid,
        })
      },
    })

    // 返回临时值（异步读取完成前用占位符）
    return this._cachedUserId || ''
  },

  /**
   * 初始化用户身份（异步，应在 onInit 中调用）
   * @returns {Promise<string>} user_id
   */
  initUserId() {
    return new Promise((resolve) => {
      storage.get({
        key: KEYS.USER_ID,
        success: (data) => {
          this._cachedUserId = data
          resolve(data)
        },
        fail: () => {
          const uuid = generateUUID()
          this._cachedUserId = uuid
          storage.set({
            key: KEYS.USER_ID,
            value: uuid,
            success: () => resolve(uuid),
            fail: () => resolve(uuid),
          })
=======
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
>>>>>>> si
        },
      })
    })
  },

<<<<<<< HEAD
  /**
   * 获取昵称（同步）
   * @returns {string}
   */
  getNickname() {
    if (this._cachedNickname) return this._cachedNickname
    return ''
  },

  /**
   * 初始化昵称
   * @returns {Promise<string>}
   */
  initNickname() {
    return new Promise((resolve) => {
      storage.get({
        key: KEYS.NICKNAME,
        success: (data) => {
          this._cachedNickname = data
          resolve(data)
        },
        fail: () => {
          resolve('')
        },
      })
    })
  },

  /**
   * 设置昵称（注册后调用）
   * @param {string} nickname
   */
  setNickname(nickname) {
    this._cachedNickname = nickname
    storage.set({
      key: KEYS.NICKNAME,
      value: nickname,
    })
  },

  /**
   * 检查是否已注册（有昵称即为已注册）
   * @returns {Promise<boolean>}
   */
  isRegistered() {
    return new Promise((resolve) => {
      storage.get({
        key: KEYS.NICKNAME,
        success: (data) => {
          resolve(!!data)
        },
        fail: () => resolve(false),
      })
    })
=======
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
>>>>>>> si
  },
}
