/**
 * 家庭成员档案 API
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 获取全部档案列表
   * @returns {Promise<{profiles:Array, total:number}>}
   */
  list() {
    return $ajax.get(`${baseUrl}/profiles`)
  },

  /**
   * 创建档案
   * @param {Object} data - { name, relation?, birth_date?, avatar_url?, content_md? }
   * @returns {Promise<{id, name, relation, ...}>}
   */
  create(data) {
    return $ajax.post(`${baseUrl}/profiles`, data)
  },

  /**
   * 更新档案
   * @param {number} profileId
   * @param {Object} data - 要更新的字段（全可选）
   * @returns {Promise<{id, name, relation, ...}>}
   */
  update(profileId, data) {
    return $ajax.put(`${baseUrl}/profiles/${profileId}`, data)
  },

  /**
   * 删除档案
   * @param {number} profileId
   * @returns {Promise}
   */
  remove(profileId) {
    return $ajax.delete(`${baseUrl}/profiles/${profileId}`)
  },
}
