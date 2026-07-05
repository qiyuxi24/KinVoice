/**
 * AI 档案编写 API
<<<<<<< HEAD
=======
 *
 * user_id 由 ajax.js 自动通过 X-User-Id Header 注入，无需手动传递。
>>>>>>> si
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 从今日对话自动更新动态档案（Companion onHide 时调用）
<<<<<<< HEAD
   * @param {string} [userId='default']
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateDynamic(userId = 'default') {
    return $ajax.post(`${baseUrl}/profile/ai/update-dynamic`, { user_id: userId })
=======
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateDynamic() {
    return $ajax.post(`${baseUrl}/profile/ai/update-dynamic`, {})
>>>>>>> si
  },

  /**
   * 更新固定档案（Profile 页面手动触发）
<<<<<<< HEAD
   * @param {string} [userId='default']
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateStable(userId = 'default') {
    return $ajax.post(`${baseUrl}/profile/ai/update-stable`, { user_id: userId })
=======
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateStable() {
    return $ajax.post(`${baseUrl}/profile/ai/update-stable`, {})
>>>>>>> si
  },

  /**
   * 读取用户档案
<<<<<<< HEAD
   * @param {string} [userId='default']
   * @returns {Promise<{user_id, stable, dynamic}>}
   */
  read(userId = 'default') {
    return $ajax.get(`${baseUrl}/profile/ai/read`, { user_id: userId })
=======
   * @returns {Promise<{user_id, stable, dynamic}>}
   */
  read() {
    return $ajax.get(`${baseUrl}/profile/ai/read`)
>>>>>>> si
  },
}
