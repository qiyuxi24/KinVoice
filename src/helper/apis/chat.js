import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  sendMessage(data) {
    return $ajax.post(`${baseUrl}/chat`, {
      message: data.message,
      history: data.history || [],
      emotion_state: data.emotionState || null,
    })
  },
}