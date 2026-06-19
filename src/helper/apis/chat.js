import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 发送消息给 Cloudie，获取 NVC 风格回复
   * @param {Object} data - { message, history?, emotionState? }
   * @returns {Promise<{reply, emotion?, need_hint?}>}
   *
   * 可能错误码：
   *   1001 — 后端未启动
   *   2001 — 请求超时
   *   4002 — LLM 调用失败（Mock 模式下不会出现）
   */
  sendMessage(data) {
    return $ajax.post(`${baseUrl}/chat`, {
      message: data.message,
      history: data.history || [],
      emotion_state: data.emotionState || null,
    })
  },
}