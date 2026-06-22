/**
 * NVC 非暴力沟通转换 API
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  /**
   * 将原始文本转换为 NVC 四要素
   * @param {Object} params - { text: string }
   * @returns {Promise<{observation, feeling, need, request, full_expression}>}
   */
  convert(params) {
    return $ajax.post(`${baseUrl}/convert`, params)
  },
}
