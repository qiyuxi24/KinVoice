import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 将原始文本转换为 NVC 温柔表达
   * @param {Object} data - { rawText }
   * @returns {Promise<{original, converted, tokens_used, processing_time}>}
   */
  transform(data) {
    return $ajax.post(`${baseUrl}/convert`, {
      raw_text: data.rawText,
    })
  },
}