/**
<<<<<<< HEAD
 * 家庭成员档案 API
=======
 * 用户个人文档 API
 * user_id 由 ajax.js 自动通过 X-User-Id Header 注入
>>>>>>> si
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
<<<<<<< HEAD
   * 获取全部档案列表
=======
   * 获取当前用户的全部文档列表
>>>>>>> si
   * @returns {Promise<{profiles:Array, total:number}>}
   */
  list() {
    return $ajax.get(`${baseUrl}/profiles`)
  },

  /**
<<<<<<< HEAD
   * 创建档案
   * @param {Object} data - { name, relation?, birth_date?, avatar_url?, content_md? }
   * @returns {Promise<{id, name, relation, ...}>}
=======
   * 创建文档
   * @param {Object} data - { name, tags?, content_md? }
   * @returns {Promise<{id, user_id, name, tags, content_md, ...}>}
>>>>>>> si
   */
  create(data) {
    return $ajax.post(`${baseUrl}/profiles`, data)
  },

  /**
<<<<<<< HEAD
   * 更新档案
   * @param {number} profileId
   * @param {Object} data - 要更新的字段（全可选）
   * @returns {Promise<{id, name, relation, ...}>}
=======
   * 更新文档
   * @param {number} profileId
   * @param {Object} data - 要更新的字段（全可选）
   * @returns {Promise<{id, name, tags, content_md, ...}>}
>>>>>>> si
   */
  update(profileId, data) {
    return $ajax.put(`${baseUrl}/profiles/${profileId}`, data)
  },

  /**
<<<<<<< HEAD
   * 删除档案
=======
   * 删除文档
>>>>>>> si
   * @param {number} profileId
   * @returns {Promise}
   */
  remove(profileId) {
    return $ajax.delete(`${baseUrl}/profiles/${profileId}`)
  },
}
