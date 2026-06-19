/**
 * 您可以将常用的方法、或系统 API，统一封装，暴露全局，以便各页面、组件调用，而无需 require / import.
 */
const prompt = require('@system.prompt')

/**
 * 拼接 url 和参数
 */
function queryString(url, query) {
  if (!query) {
    return url
  }

  let str = []
  for (let key in query) {
    if (query[key] === null || typeof query[key] === 'undefined' || query[key] === '') {
      continue
    }
    str.push(`${encodeURIComponent(key)}=${encodeURIComponent(query[key])}`)
  }
  let paramStr = str.join('&')
  return paramStr ? `${url}?${paramStr}` : url
}

function showToast(message = '', duration = 0) {
  if (!message) return
  prompt.showToast({
    message: message,
    duration
  })
}

export default {
  showToast,
  queryString
}
