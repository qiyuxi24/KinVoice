/**
 * AI 陪伴对话 API
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 发送消息，获取 AI 回复
   * @param {Object} params - { message: string }
   * @returns {Promise<{reply: string}>}
   */
  sendMessage(params) {
    return $ajax.post(`${baseUrl}/chat`, params)
  },
}
