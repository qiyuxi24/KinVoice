import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 获取卡片列表
   * @param {Object} [params] - { category?, limit?, offset? }
   * @returns {Promise<{cards:Array, total:number}>}
   *
   * 可能错误码：1001, 2001, 4001
   */
  list(params) {
    return $ajax.get(`${baseUrl}/cards`, {
      category: params && params.category,
      limit: params && params.limit ? params.limit : 20,
      offset: params && params.offset ? params.offset : 0,
    })
  },

  /**
   * 创建新卡片
   * @param {Object} data - { category, emotion, observation, feeling, need, request?, title?, content?, author?, tag? }
   * @returns {Promise<{id, category, ...}>}
   *
   * 可能错误码：1001, 2001, 3004(422), 4001
   */
  create(data) {
    return $ajax.post(`${baseUrl}/cards`, data)
  },

  /**
   * 更新卡片
   * @param {number} cardId
   * @param {Object} data - 要更新的字段（全可选）
   * @returns {Promise<{id, category, ...}>}
   *
   * 可能错误码：1001, 2001, 3003(404), 4001
   */
  update(cardId, data) {
    return $ajax.put(`${baseUrl}/cards/${cardId}`, data)
  },

  /**
   * 删除卡片
   * @param {number} cardId
   * @returns {Promise}
   *
   * 可能错误码：1001, 2001, 3003(404), 4001
   */
  remove(cardId) {
    return $ajax.delete(`${baseUrl}/cards/${cardId}`)
  },

  /**
   * 双向同步：本地全部卡片 ↔ 后端
   * @param {Object[]} cards - 本地缓存的全部卡片 [{id?, tag, date, title, author, content, emotion, need}, ...]
   * @returns {Promise<{cards:Array, added_to_backend:number, added_to_local:number, total:number}>}
   *
   * 只增不减：本地有后端没有的 → 创建到后端；后端有本地没有的 → 返回给前端
   */
  sync(cards) {
    return $ajax.post(`${baseUrl}/cards/sync`, { cards: cards })
  },
}