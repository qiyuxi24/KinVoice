/**
 * 封装了网络请求方法，集成错误码体系
 * - 自动解析 HTTP 状态码 → 业务错误码
 * - 统一错误格式：{ code, message, detail, level, raw }
 * - 支持 GET / POST / PUT / DELETE
 */
import $fetch from '@system.fetch'
import $utils from './utils'
import { getErrorInfo, mapDetailToCode, httpStatusToCode, fetchErrorToCode } from './errorCodes'
import userIdentity from './userIdentity'

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

function buildError(code, raw, extraMsg) {
  const info = getErrorInfo(code)
  return {
    code: code,
    message: extraMsg || info.message,
    detail: info.detail,
    level: info.level,
    raw: raw,
    isError: true,
  }
}

function parseBackendError(responseData, statusCode) {
  if (statusCode >= 200 && statusCode < 300) {
    return null
  }
  const backendDetail = (responseData && responseData.detail) || ''
  const bizCode = mapDetailToCode(backendDetail)
  if (bizCode) {
    return buildError(bizCode, responseData, backendDetail)
  }
  return buildError(httpStatusToCode(statusCode), responseData, backendDetail)
}

function fetchPromise(params) {
  return new Promise((resolve, reject) => {
    const fetchOptions = {
      url: params.url,
      method: params.method,
      header: params.header || {},
    }
    const uid = userIdentity.getUserId()
    if (uid) {
      fetchOptions.header['X-User-Id'] = uid
    }
    if (params.data !== undefined && params.data !== null) {
      if (typeof params.data === 'string') {
        fetchOptions.data = params.data
      } else {
        fetchOptions.data = JSON.stringify(params.data)
        fetchOptions.header['Content-Type'] = 'application/json'
      }
    }
    $fetch
      .fetch(fetchOptions)
      .then(response => {
        const rawText = response.data
        let parsed = null
        try {
          parsed = JSON.parse(rawText)
        } catch (e) {
          resolve(rawText)
          return
        }
        if (parsed && typeof parsed === 'object' &&
            typeof parsed.data === 'string' &&
            parsed.headers && typeof parsed.headers === 'object') {
          try {
            parsed = JSON.parse(parsed.data)
          } catch (e) {}
        }
        const err = parseBackendError(parsed, response.code)
        if (err) {
          reject(err)
        } else {
          resolve(parsed)
        }
      })
      .catch((error, code) => {
        const errCode = fetchErrorToCode(code)
        const err = buildError(errCode, error)
        reject(err)
      })
  })
}

function requestHandle(params, timeout = TIMEOUT) {
  let timerId = null
  const timeoutPromise = new Promise((resolve, reject) => {
    timerId = setTimeout(() => {
      timerId = null
      reject(buildError(1001, null, '请求超时（' + (timeout / 1000) + 's）'))
    }, timeout)
  })
  return Promise.race([fetchPromise(params), timeoutPromise])
    .finally(() => {
      if (timerId) {
        clearTimeout(timerId)
        timerId = null
      }
    })
}

// ========== 新增：支持任意 responseType 的原始请求（用于下载二进制数据） ==========
function rawRequest({ url, method, data, header, responseType = 'text' }) {
  return new Promise((resolve, reject) => {
    const fetchOptions = { url, method, header: header || {} }
    const uid = userIdentity.getUserId()
    if (uid) fetchOptions.header['X-User-Id'] = uid
    if (data !== undefined && data !== null) {
      fetchOptions.data = typeof data === 'string' ? data : JSON.stringify(data)
      fetchOptions.header['Content-Type'] = 'application/json'
    }
    fetchOptions.responseType = responseType

    let timerId = null
    const timeout = TIMEOUT
    const timeoutPromise = new Promise((_, rej) => {
      timerId = setTimeout(() => {
        timerId = null
        rej(buildError(1001, null, '请求超时'))
      }, timeout)
    })

    const fetchTask = $fetch.fetch(fetchOptions)
      .then(response => {
        resolve(response.data)
      })
      .catch((err, code) => {
        reject({ error: err, code })
      })

    Promise.race([fetchTask, timeoutPromise])
      .catch(err => {
        if (err && err.isError) reject(err)
        else reject(buildError(1001, null))
      })
      .finally(() => {
        if (timerId) clearTimeout(timerId)
      })
  })
}

export default {
  post: function(url, params) {
    return requestHandle({ method: 'post', url: url, data: params })
  },
  get: function(url, params) {
    return requestHandle({ method: 'get', url: $utils.queryString(url, params) })
  },
  put: function(url, params) {
    return requestHandle({ method: 'put', url: url, data: params })
  },
  delete: function(url, params) {
    return requestHandle({ method: 'delete', url: url, data: params })
  },
  rawRequest   // ← 确保导出
}