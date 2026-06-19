/**
 * API 错误码表
 *
 * 分类规则：
 *   1xxx — 网络 / 连接错误
 *   2xxx — 超时错误
 *   3xxx — HTTP 客户端错误 (4xx)
 *   4xxx — 服务端错误 (5xx)
 *   5xxx — 数据 / 解析错误
 */

var ERROR_CODES = {
  /* ---------- 1xxx 网络 ---------- */
  'ERR_NETWORK':        { code: 1001, message: '网络连接失败，后端未启动或 baseUrl 配置错误' },
  'ERR_DNS':            { code: 1002, message: 'DNS 解析失败，请检查域名或网络' },

  /* ---------- 2xxx 超时 ---------- */
  'ERR_TIMEOUT':        { code: 2001, message: '请求超时，后端响应过慢或网络不通' },

  /* ---------- 3xxx 客户端 ---------- */
  'ERR_BAD_REQUEST':    { code: 3001, message: '请求参数格式有误 (400)' },
  'ERR_UNAUTHORIZED':   { code: 3002, message: '未授权，请检查 API Key (401)' },
  'ERR_NOT_FOUND':      { code: 3003, message: '接口路径不存在 (404)' },
  'ERR_VALIDATION':     { code: 3004, message: '请求字段校验失败 (422)' },
  'ERR_TOO_MANY':       { code: 3005, message: '请求过于频繁，请稍后重试 (429)' },

  /* ---------- 4xxx 服务端 ---------- */
  'ERR_SERVER':         { code: 4001, message: '服务器内部错误 (500)' },
  'ERR_LLM_FAIL':       { code: 4002, message: '大模型调用失败或超时' },
  'ERR_UNAVAILABLE':    { code: 4003, message: '服务暂不可用 (503)' },

  /* ---------- 5xxx 数据 ---------- */
  'ERR_PARSE':          { code: 5001, message: '响应数据格式异常，无法解析' },
  'ERR_EMPTY_RESP':     { code: 5002, message: '响应数据为空' },
  'ERR_MISSING_FIELD':  { code: 5003, message: '响应缺少必要字段' },

  /* ---------- 通用 ---------- */
  'ERR_UNKNOWN':        { code: 9999, message: '未知错误' }
}

/**
 * 根据 HTTP 状态码匹配错误码
 * @param {number} statusCode
 * @returns {object} { code, message }
 */
function codeFromStatus(statusCode) {
  var map = {
    400: 'ERR_BAD_REQUEST',
    401: 'ERR_UNAUTHORIZED',
    404: 'ERR_NOT_FOUND',
    422: 'ERR_VALIDATION',
    429: 'ERR_TOO_MANY',
    500: 'ERR_SERVER',
    503: 'ERR_UNAVAILABLE'
  }
  var key = map[statusCode] || 'ERR_SERVER'
  return ERROR_CODES[key]
}

/**
 * 根据错误对象判定错误码
 * @param {Error} error
 * @param {number} [httpStatus]
 * @returns {{ code: number, message: string, type: string }}
 */
function classifyError(error, httpStatus) {
  if (!error) {
    return Object.assign({ type: 'ERR_UNKNOWN' }, ERROR_CODES['ERR_UNKNOWN'])
  }

  // 超时
  if (error.name === 'TimeoutError') {
    return Object.assign({ type: 'ERR_TIMEOUT' }, ERROR_CODES['ERR_TIMEOUT'])
  }

  // HTTP 错误
  if (error.name === 'HttpError' || httpStatus) {
    var status = httpStatus || error.statusCode || 0
    var result = codeFromStatus(status)

    // 500 且消息包含 LLM 关键词
    if (status === 500 && error.message && (error.message.indexOf('LLM') !== -1 || error.message.indexOf('大模型') !== -1)) {
      result = ERROR_CODES['ERR_LLM_FAIL']
    }
    return Object.assign({ type: result === ERROR_CODES['ERR_SERVER'] ? 'ERR_SERVER' : 'ERR_VALIDATION' }, result)
  }

  // 网络错误（后端未启动）
  if (error.message && error.message.indexOf('fetch') !== -1) {
    return Object.assign({ type: 'ERR_NETWORK' }, ERROR_CODES['ERR_NETWORK'])
  }

  return Object.assign({ type: 'ERR_NETWORK' }, ERROR_CODES['ERR_NETWORK'])
}

export default {
  ERROR_CODES: ERROR_CODES,
  codeFromStatus: codeFromStatus,
  classifyError: classifyError
}
