# 通信层 API 文档

## 架构概览

三层通信架构，从底层网络封装到上层业务接口：

```
页面 (pages/*.ux)
  │  $apis.chat.sendMessage() / $apis.convert.transform()
  ▼
第二层：接口模块 (apis/*.js) —— 每个后端接口一个文件
  │  $ajax.post() / $ajax.get() / $ajax.delete()
  ▼
第一层：底层封装 (ajax.js) —— Promise 封装 @system.fetch
  │  @system.fetch
  ▼
FastAPI 后端 (backend/app/)
```

全局注入 (`app.ux`)：

```js
const $utils = require('./helper/utils').default
const $apis = require('./helper/apis').default
const hook2global = global.__proto__ || global
hook2global.$utils = $utils
hook2global.$apis = $apis
```

---

## 第一层：`helper/ajax.js` — 底层网络封装

基于快应用 `@system.fetch` 的 Promise 封装。主要负责：超时控制、JSON 序列化/反序列化、错误统一处理。

### 快应用适配要点

`@system.fetch` 返回结构与标准 fetch 不同：

```js
// 快应用返回结构（非标准）
{
  code: 200,           // HTTP 状态码（模拟器可能为 0）
  headers: { ... },    // 响应头
  data: "..."          // 响应体（JSON 字符串）
}
```

针对这一特点做了两层适配：
1. `normalizeData()` 尝试 JSON.parse 响应体
2. 若解析后仍为原始结构（含 `code`/`data` 字段），则对 `data` 字段**二次解析**
3. `code` 为 0 但有响应数据时仍视为成功（兼容模拟器）

### 对外方法

| 方法 | HTTP | 签名 | 说明 |
|------|------|------|------|
| `$ajax.post(url, data)` | POST | `(string, object) → Promise` | 发送 JSON 请求体 |
| `$ajax.get(url, params)` | GET | `(string, object?) → Promise` | 参数拼接到 URL query string |
| `ajax.put(url, data)` | PUT | `(string, object) → Promise` | 更新资源 |
| `ajax.delete(url, params)` | DELETE | `(string, object?) → Promise` | 删除资源，可选 query 参数 |

> 注意：`$ajax` 是 `helper/ajax.js` 的默认导出，在 `apis/*.js` 中以 `$ajax` 引用，页面不直接使用。

### 内部流程

```
$ajax.post(url, data)
  → requestHandle({ method:'post', url, data })
    → Promise.race([
        fetchPromise(params),          // 实际请求
        setTimeout(20s, reject)        // 超时竞速
      ])
      → $fetch.fetch({ url, method, data, header })
        → .then(response)
          → normalizeData(response.data)    // 一次解析
          → 检测是否含 code/data 二次解析    // 二次兜底
          → 2xx 或 有数据 → resolve(body)
          → 否则 → reject(HttpError)
        → .catch → reject(Error)
```

### 错误类型

| 类型 | `name` | 触发条件 |
|------|--------|----------|
| `HttpError` | `'HttpError'` | 服务端返回非 2xx 且无响应体 |
| `Error` | `'Error'` | 网络不可达（`@system.fetch` 抛异常） |
| `Error` | `'Error'` | 超时（20 秒无响应） |

### 超时

- 默认 20 秒（`TIMEOUT = 20000`）
- 通过 `Promise.race` 实现
- 超时后页面收到 `.catch()` 回调

---

## 第二层：`helper/apis/` — 接口模块

通过 `index.js` 的 `require.context` 自动扫描目录下所有 `.js` 文件（排除自身），挂载到 `$apis` 全局对象。

### `config.js` — Base URL

```js
// src/helper/apis/config.js
const previewBaseUrl = 'http://localhost:8000'
export default { baseUrl: previewBaseUrl }
```

| 场景 | baseUrl |
|------|---------|
| IDE 模拟器预览 | `http://localhost:8000` |
| USB 真机调试 | `http://192.168.x.x:8000`（局域网 IP） |
| 生产环境 | `https://api.xxx.com` |

### `chat.js` — 陪伴对话

```js
$apis.chat.sendMessage({
  message: '今天好累',
  history: [{ role: 'user', content: '...' }],  // 可选
  emotionState: '疲惫',                           // 可选
})
// → Promise<{ reply: string, emotion?: string, need_hint?: string }>
```

| 属性 | 方向 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `message` | 请求 | `string` | ✅ | 用户消息，1-2000 字 |
| `history` | 请求 | `array` | ❌ | 对话历史 `[{role, content}]` |
| `emotionState` → `emotion_state` | 请求 | `string` | ❌ | 情绪状态 |
| `reply` | 响应 | `string` | — | AI 的 NVC 风格回复 |
| `emotion` | 响应 | `string?` | — | 识别到的情绪 |
| `need_hint` | 响应 | `string?` | — | NVC 需求提示 |

常见错误码：`1001`（后端未启动）、`2001`（超时）、`4002`（LLM 调用失败）

### `convert.js` — 破冰转换

```js
$apis.convert.transform({ rawText: '你们从来都不理解我！' })
// → Promise<{ original, converted, tokens_used, processing_time }>
```

| 属性 | 方向 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `rawText` → `raw_text` | 请求 | `string` | ✅ | 原始文本，1-500 字 |
| `original` | 响应 | `string` | — | 原文 |
| `converted` | 响应 | `string` | — | NVC 转换后的温柔表达 |
| `tokens_used` | 响应 | `number` | — | 消耗的 token 数 |
| `processing_time` | 响应 | `number` | — | 处理耗时（秒） |

> ✅ 破冰页已通过此接口完成前后端通信验证。

### `cards.js` — 经验卡片 CRUD

```js
// 列表
$apis.cards.list({ category: '人生阅历', limit: 20, offset: 0 })
// → Promise<{ cards: CardOut[], total: number }>

// 创建
$apis.cards.create({
  category: '人生阅历',
  emotion: '感慨',
  observation: '关于工作的思考',
  feeling: '感觉很充实',
  need: '被认可',
  request: '可以多聊聊吗'
})
// → Promise<CardOut>

// 删除
$apis.cards.remove(cardId)
// → Promise<void>
```

| 方法 | HTTP | 路径 | 常见错误码 |
|------|------|------|-----------|
| `list(params)` | GET | `/cards?category=&limit=&offset=` | 1001, 2001, 4001 |
| `create(data)` | POST | `/cards` | 1001, 2001, 3004, 4001 |
| `remove(cardId)` | DELETE | `/cards/{id}` | 1001, 2001, 3003, 4001 |

> ⚠️ 此接口后端尚未注册路由，前端已做本地存储兜底。

### `errorCodes.js` — 错误码表

通过 `$apis.errorCodes` 访问：

```js
var info = $apis.errorCodes.classifyError(error, httpStatus)
// → { code: 1001, message: '网络连接失败，...', type: 'ERR_NETWORK' }
```

#### 错误码对照表

| 类型 | 错误码 | 常量 | 说明 |
|------|--------|------|------|
| 网络 | `1001` | `ERR_NETWORK` | 后端未启动或 baseUrl 配置错误 |
| 网络 | `1002` | `ERR_DNS` | DNS 解析失败 |
| 超时 | `2001` | `ERR_TIMEOUT` | 请求超时（>20s） |
| HTTP 4xx | `3001` | `ERR_BAD_REQUEST` | 请求参数格式有误 (400) |
| HTTP 4xx | `3002` | `ERR_UNAUTHORIZED` | 未授权 (401) |
| HTTP 4xx | `3003` | `ERR_NOT_FOUND` | 接口路径不存在 (404) |
| HTTP 4xx | `3004` | `ERR_VALIDATION` | 字段校验失败 (422) |
| HTTP 4xx | `3005` | `ERR_TOO_MANY` | 请求过于频繁 (429) |
| HTTP 5xx | `4001` | `ERR_SERVER` | 服务器内部错误 (500) |
| HTTP 5xx | `4002` | `ERR_LLM_FAIL` | 大模型调用失败 |
| HTTP 5xx | `4003` | `ERR_UNAVAILABLE` | 服务暂不可用 (503) |
| 数据 | `5001` | `ERR_PARSE` | 响应格式异常，JSON 解析失败 |
| 数据 | `5002` | `ERR_EMPTY_RESP` | 响应数据为空 |
| 数据 | `5003` | `ERR_MISSING_FIELD` | 响应缺少必要字段 |
| 通用 | `9999` | `ERR_UNKNOWN` | 未知错误 |

#### 使用方式

```js
$apis.chat.sendMessage({ message: '你好' })
  .then(data => { /* 处理响应 */ })
  .catch(error => {
    var info = $apis.errorCodes.classifyError(error)
    console.log('错误码: ' + info.code)     // 1001
    console.log('错误类型: ' + info.type)    // ERR_NETWORK
    $utils.showToast(info.message)           // 用户可读提示
  })
```

---

## 第三层：页面调用

所有页面通过全局 `$apis` 直接调用，无需 import。

### 陪伴页 (Companion) 调用模式

```js
callCloudieAPI(message) {
    chatAPI.sendMessage({ message: message })
      .then(data => {
        if (data && data.reply) {
          this.currentSpeech = data.reply    // 在线：显示 AI 回复
        }
      })
      .catch(error => {
        this.currentSpeech = this.getFallbackReply(message)  // 离线兜底
      })
}
```

### 破冰页 (BreakIce) 调用模式

```js
transformText() {
    $apis.convert.transform({ rawText: content })
      .then(data => {
        if (data && data.converted) {
          this.transformedText = data.converted  // 显示 NVC 温柔表达
        }
      })
      .catch(error => {
        $utils.showToast('网络请求失败')
      })
}
```

### 传承页 (Memory) 调用模式

```js
// 在线优先 + 本地兜底
loadCards() {
    $apis.cards.list({ limit: 100 })
      .then(resp => { /* 合并后端数据 */ })
      .catch(err => { this.loadCardsFromLocal() })  // 离线兜底
}

// 本地优先 + 后台同步
saveCard() {
    this.cards[key].unshift(newCard)
    this.saveCardsToLocal()                       // 本地即时生效
    $apis.cards.create(cardToBackend(newCard))     // 后台非阻塞同步
      .catch(err => console.log('后端同步失败（已存本地）'))
}
```

---

## 文件索引

```
src/helper/
├── ajax.js           # 第一层：底层网络封装
├── utils.js           # 全局工具（showToast, queryString）
└── apis/
    ├── index.js       # 自动扫描加载，挂载到 $apis
    ├── config.js      # baseUrl 配置（localhost:8000）
    ├── chat.js        # POST /chat — 陪伴对话
    ├── convert.js     # POST /convert — 破冰转换 ✅ 已打通
    ├── cards.js       # CRUD /cards — 经验卡片
    ├── errorCodes.js  # 错误码表 + classifyError()
    └── example.js     # 新增接口模板
```
