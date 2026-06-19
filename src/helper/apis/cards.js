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
   * @param {Object} data - { category, emotion, observation, feeling, need, request? }
   * @returns {Promise<{id, category, ...}>}
   *
   * 可能错误码：1001, 2001, 3004(422), 4001
   */
  create(data) {
    return $ajax.post(`${baseUrl}/cards`, data)
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
}