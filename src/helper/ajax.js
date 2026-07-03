/**
 * 封装了网络请求方法，集成错误码体系
 * - 自动解析 HTTP 状态码 → 业务错误码
 * - 统一错误格式：{ code, message, detail, level, raw }
 * - 支持 GET / POST / PUT / DELETE
 */
import $fetch from '@system.fetch'
import $utils from './utils'
import { getErrorInfo, mapDetailToCode, httpStatusToCode, fetchErrorToCode } from './errorCodes'

const TIMEOUT = 20000

if (!Promise.prototype.finally) {
  Promise.prototype.finally = function(callback) {
    const P = this.constructor
    return this.then(
      value => P.resolve(callback()).then(() => value),
      reason =>
        P.resolve(callback()).then(() => {
          throw reason
        })
    )
  }
}

/**
 * 构造统一错误对象
 * @param {number} code     - 错误码
 * @param {*}      raw      - 原始数据（响应体 / Error 对象）
 * @param {string} extraMsg - 额外补充消息（后端 detail）
 * @returns {{ code: number, message: string, detail: string, level: string, raw: * }}
 */
function buildError(code, raw, extraMsg) {
  const info = getErrorInfo(code)
  return {
    code: code,
    message: extraMsg || info.message,
    detail: info.detail,
    level: info.level,
    raw: raw,
    isError: true,                  // 快速判断标记
  }
}

/**
 * 解析后端 JSON 响应，提取可能的错误信息
 * @param {object} responseData - 已 parse 的 JSON 对象
 * @param {number} statusCode   - HTTP 状态码
 * @returns {{ code: number, message: string, detail: string, level: string }|null}
 *         返回 null 表示成功（2xx），否则返回错误对象
 */
function parseBackendError(responseData, statusCode) {
  // 2xx 视为成功
  if (statusCode >= 200 && statusCode < 300) {
    return null
  }

  // 尝试从后端 detail 字段映射业务错误码
  const backendDetail = (responseData && responseData.detail) || ''
  const bizCode = mapDetailToCode(backendDetail)

  if (bizCode) {
    return buildError(bizCode, responseData, backendDetail)
  }

  // 兜底：HTTP 状态码 → 通用错误码
  return buildError(httpStatusToCode(statusCode), responseData, backendDetail)
}

/**
 * 调用快应用 fetch 接口做网络请求
 * 成功 → resolve(后端 JSON)
 * 失败 → reject({ code, message, detail, level, raw, isError })
 */
function fetchPromise(params) {
  return new Promise((resolve, reject) => {
    $fetch
      .fetch({
        url: params.url,
        method: params.method,
        data: params.data,
      })
      .then(response => {
        // 快应用 @system.fetch 返回: { code: 200, data: "JSON字符串", headers: {} }
        const rawText = response.data
        let parsed = null

        try {
          parsed = JSON.parse(rawText)
        } catch (e) {
          // JSON 解析失败 → 视为成功（可能是二进制数据，如 TTS）
          console.log('[ajax] 响应非 JSON，可能是二进制数据')
          resolve(rawText)
          return
        }

        // 检查后端是否返回了错误
        const err = parseBackendError(parsed, response.code)
        if (err) {
          reject(err)
        } else {
          resolve(parsed)
        }
      })
      .catch((error, code) => {
        // 快应用 fetch 层错误（网络层）
        const errCode = fetchErrorToCode(code)
        const err = buildError(errCode, error)
        console.log(`🐛 [${errCode}] ${err.message} | code=${code}`)
        reject(err)
      })
      .finally(() => {
        console.log(`✔️ ${params.method} @${params.url} 完成`)
      })
  })
}

/**
 * 处理网络请求，带超时保护
 * @param {object} params  - { url, method, data }
 * @param {number} timeout - 超时时间 ms
 * @returns {Promise}
 */
function requestHandle(params, timeout = TIMEOUT) {
  try {
    return Promise.race([
      fetchPromise(params),
      new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(buildError(1001, null, '请求超时（' + (timeout / 1000) + 's）'))
        }, timeout)
      }),
    ])
  } catch (error) {
    console.log('[ajax] requestHandle 异常:', error)
    return Promise.reject(buildError(1099, error))
  }
}

// ── 导出的 HTTP 方法 ──

export default {
  /** POST 请求 */
  post: function(url, params) {
    return requestHandle({
      method: 'post',
      url: url,
      data: params,
    })
  },

  /** GET 请求 */
  get: function(url, params) {
    return requestHandle({
      method: 'get',
      url: $utils.queryString(url, params),
    })
  },

  /** PUT 请求 */
  put: function(url, params) {
    return requestHandle({
      method: 'put',
      url: url,
      data: params,
    })
  },

  /** DELETE 请求 */
  delete: function(url, params) {
    return requestHandle({
      method: 'delete',
      url: url,
      data: params,
    })
  },
}
