/**
 * AI 档案编写 API
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 从今日对话自动更新动态档案（Companion onHide 时调用）
   * @param {string} [userId='default']
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateDynamic(userId = 'default') {
    return $ajax.post(`${baseUrl}/profile/ai/update-dynamic`, { user_id: userId })
  },

  /**
   * 更新固定档案（Profile 页面手动触发）
   * @param {string} [userId='default']
   * @returns {Promise<{ok, profile_type, path, content_preview, messages_used}>}
   */
  updateStable(userId = 'default') {
    return $ajax.post(`${baseUrl}/profile/ai/update-stable`, { user_id: userId })
  },

  /**
   * 读取用户档案
   * @param {string} [userId='default']
   * @returns {Promise<{user_id, stable, dynamic}>}
   */
  read(userId = 'default') {
    return $ajax.get(`${baseUrl}/profile/ai/read`, { user_id: userId })
  },
}
