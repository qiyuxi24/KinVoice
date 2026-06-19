import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  transform(data) {
    return $ajax.post(`${baseUrl}/convert`, {
      raw_text: data.rawText,
      emotion_hint: data.emotionHint || null,
    })
  },
}