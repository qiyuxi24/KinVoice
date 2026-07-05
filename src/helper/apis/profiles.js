/**
 * 用户个人文档 API
 * user_id 由 ajax.js 自动通过 X-User-Id Header 注入
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 获取当前用户的全部文档列表
   * @returns {Promise<{profiles:Array, total:number}>}
   */
  list() {
    return $ajax.get(`${baseUrl}/profiles`)
  },

  /**
   * 创建文档
   * @param {Object} data - { name, tags?, content_md? }
   * @returns {Promise<{id, user_id, name, tags, content_md, ...}>}
   */
  create(data) {
    return $ajax.post(`${baseUrl}/profiles`, data)
  },

  /**
   * 更新文档
   * @param {number} profileId
   * @param {Object} data - 要更新的字段（全可选）
   * @returns {Promise<{id, name, tags, content_md, ...}>}
   */
  update(profileId, data) {
    return $ajax.put(`${baseUrl}/profiles/${profileId}`, data)
  },

  /**
   * 删除文档
   * @param {number} profileId
   * @returns {Promise}
   */
  remove(profileId) {
    return $ajax.delete(`${baseUrl}/profiles/${profileId}`)
  },
}