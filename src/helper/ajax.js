/**
 * 封装了一些网络请求方法，方便通过 Promise 的形式请求接口
 */
import $fetch from '@system.fetch'
import $utils from './utils'

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

function normalizeData(data) {
  if (!data) {
    return data
  }

  if (typeof data === 'string') {
    try {
      return JSON.parse(data)
    } catch (error) {
      return data
    }
  }

  return data
}

function buildRequestData(method, data) {
  if (method === 'get' || typeof data === 'undefined' || data === null) {
    return data
  }

  return JSON.stringify(data)
}

function buildErrorMessage(response) {
  const payload = normalizeData(response.data)
  const debugHint = '；请确认后端已启动，真机调试时把 baseUrl 改成电脑局域网 IP:18000'
  if (payload && payload.detail) {
    return `${payload.detail}${debugHint}`
  }
  if (payload && payload.message) {
    return `${payload.message}${debugHint}`
  }
  return `请求失败（${response.code || 'unknown'}）${debugHint}`
}

/**
 * 调用快应用 fetch 接口做网络请求
 * @param params
 */
function fetchPromise(params) {
  return new Promise((resolve, reject) => {
    $fetch
      .fetch({
        url: params.url,
        method: params.method,
        data: buildRequestData(params.method, params.data),
        header: params.header || {
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        const statusCode = Number(response.code || 0)
        const content = normalizeData(response.data)

        if (statusCode >= 200 && statusCode < 300) {
          resolve(content)
        } else if (content) {
          resolve(content)
        } else {
          reject(new Error(buildErrorMessage(response)))
        }
      })
      .catch((error, code) => {
        console.log(`🐛 request fail, code = ${code}`)
        reject(
          error instanceof Error
            ? new Error(`${error.message}；请检查后端服务和 baseUrl 配置`)
            : new Error('网络请求失败；请检查后端服务和 baseUrl 配置')
        )
      })
  })
}

/**
 * 处理网络请求，timeout 是网络请求超时之后返回，默认 20s 可自行修改
 * @param params
 */
function requestHandle(params, timeout = TIMEOUT) {
  return Promise.race([
    fetchPromise(params),
    new Promise((resolve, reject) => {
      setTimeout(() => {
        reject(new Error('网络状况不太好，再刷新一次？若是真机调试，请检查局域网 IP:18000 是否可访问'))
      }, timeout)
    })
  ])
}

export default {
  post: function(url, params) {
    return requestHandle({
      method: 'post',
      url: url,
      data: params
    })
  },
  get: function(url, params) {
    return requestHandle({
      method: 'get',
      url: $utils.queryString(url, params)
    })
  },
  put: function(url, params) {
    return requestHandle({
      method: 'put',
      url: url,
      data: params
    })
  },
  delete: function(url) {
    return requestHandle({
      method: 'delete',
      url: url
    })
  }
}
