# KinVoice 项目改动记录

## 2026-06-20 — Memory 页面双向同步 + 编辑删除功能

### 需求
前端 Memory 页面改为「本地缓存优先 + 双向同步」模式：
1. 初始 mock 数据写入本地缓存
2. `onShow` 时前后端双向同步（只增不减）
3. 卡片增/改/删操作实时推后端 + 更新本地缓存
4. 前端始终从本地缓存读取渲染

### 后端改动

#### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/api/memory.py` | 新增 `POST /cards/sync` 接口 + `LocalCard`/`SyncRequest`/`SyncResult` schema。同步逻辑：本地有 id 且后端存在→跳过；本地无 id 或 id 不在后端→创建到后端；后端有但本地没有→返回给前端追加 |

#### API 新增

| 路由 | 方法 | 功能 |
|------|------|------|
| `/cards/sync` | POST | 双向同步：入参 `{cards: [{id?, tag, date, title, author, content, emotion, need}]}`，返回合并后的完整列表 + 增量统计 |

### 前端改动

#### 修改文件

| 文件 | 改动 |
|------|------|
| `src/helper/apis/cards.js` | 新增 `sync(cards)` 方法，调 `POST /cards/sync` |
| `src/pages/Memory/index.ux` | 全面重构：<br>① mock 数据移到 `INITIAL_MOCK_CARDS` 常量，首次使用时写入本地缓存<br>② `loadFromLocal()` 始终从 `@system.storage` 加载，兜底写 mock<br>③ `onShow()` 调用 `syncWithBackend()` 双向合并<br>④ 新增编辑功能：卡片上的 ✏️ 按钮 → `editCard()` → 弹窗填充已有数据 → `doUpdateCard()` 调 PUT + 更新本地<br>⑤ 新增删除功能：卡片上的 🗑️ 按钮 → `deleteCard()` 调 DELETE + 删本地<br>⑥ 弹窗支持编辑模式：标题改为「编辑经验」，按钮改为「保存修改」，增加作者输入<br>⑦ 分类变更时自动移动卡片到新分类<br>⑧ 所有操作都有离线降级（后端不可达时仅更新本地） |

### 同步策略

```
onShow() → 本地全部卡片 POST /cards/sync
  ├─ 本地有 id + 后端存在 → 跳过（只增不减）
  ├─ 本地无 id / id 不在后端 → 创建到后端，分配 id
  └─ 后端有 + 本地没有 → 追加到返回结果

前端增/改/删 → 实时调 POST/PUT/DELETE + 更新本地缓存
  └─ 失败降级：仅更新本地，下次 onShow 同步时补齐
```

### 设计决策

1. **只增不减**：同步时两端互不覆盖已有数据，避免冲突
2. **本地优先渲染**：页面始终从 `@system.storage` 读取，不阻塞 UI
3. **离线降级**：每次 API 调用失败时静默降级到本地操作，下次 onShow 自动补齐
4. **id 一致性**：创建/同步后立即用后端返回的 id 更新本地对象

---

## 2026-06-20 — 对话自动总结 → 经验卡片

### 需求
用户在 Companion 页面完成多轮对话后，自动触发 LLM 总结对话内容，生成 NVC 经验卡片存入知识库。与已有卡片比对后决定新建还是追加。

### 架构设计

```
用户多轮对话 → Companion.onHide() → POST /chat/summarize
  → 关键词提取 → SQLite LIKE 匹配候选卡片（≤10条）
  → LLM 总结 + 比对 → 返回 [{action, card_id, NVC四要素}, ...]
  → 逐条执行 create/update → 返回结果
```

### 后端改动

#### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/card_summarizer.py` | LLM 总结服务：对话→NVC卡片 JSON，含 prompt 工程 |
| `backend/app/api/summarize.py` | `POST /chat/summarize` 接口：关键词提取 + LIKE 匹配 + 调用总结服务 + 执行DB操作 |

#### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | +2行：import summarize_router + include_router |

### 前端改动

| 文件 | 改动 |
|------|------|
| `src/pages/Companion/index.ux` | `<script>` 部分新增：`chatHistory` 数组、`saveHistory()`/`restoreHistory()`/`clearHistory()` 方法、`onHide()` 钩子调用 summarize API、`onShow()` 恢复未总结历史、`sendMessage()`/`callCloudieAPI()` 中记录对话历史 |

### API 新增

| 路由 | 方法 | 功能 |
|------|------|------|
| `/chat/summarize` | POST | 对话总结→卡片（入参 `{history: [{role, content}]}`） |

### 测试结果

- ✅ 空知识库场景：多轮对话生成 1 张新卡片，NVC 四要素完整
- ✅ 已有卡片场景：LLM 正确判断新建/更新
- ✅ 手动 CRUD（POST/PUT/DELETE/GET）不受影响
- ✅ 后端零 lint 错误
- ✅ 所有已有路由正常注册

### 关键设计决策

1. **关键词 + LIKE 匹配**：用简单中文分词从对话提取关键词，SQLite `LIKE` 匹配 observation 字段，控制候选集 ≤10 条，避免 prompt 过长
2. **前端本地缓存 history**：快应用 `@system.storage` 持久化，离开页面时发送，失败不清理（下次重试）
3. **允许一次多张卡片**：LLM 返回数组，一次对话最多 3 张
4. **update 降级 create**：如果 LLM 指定的 card_id 不存在，自动降级为新建
5. **分类自动判断**：LLM 在 4 个分类中自行选择

---

## 2026-07-05 — Cloudie Agent 架构：主 Agent + 子 AI 解耦

### 架构决策
Cloudie 是主 Agent，Profile AI 和 Cards AI 是独立的子服务（各有独立 prompt + API），由后端 chat.py 编排调用：

```
前端只调 POST /chat
  → chat.py:
    ① read_profiles(user_id) → 注入 system prompt（每次对话都读）
    ② FTS search_context() → 检索传承笔记+对话历史 → 注入上下文
    ③ Cloudie LLM 生成回复
    ④ asyncio.create_task(_background_extract):
       - 每3轮 → update_dynamic_profile()（Profile AI 独立 prompt）
       - 每5轮 → summarize_to_notes() → 写入 Card 表（Cards AI 独立 prompt）
```

### 三条 AI 线
| 服务 | Prompt 文件 | 职责 |
|------|-----------|------|
| Cloudie（对话） | `cloudie_prompt.py` | 温暖陪伴 + 读档案 + 用检索结果 |
| Profile AI | `profile_writer.py` | STABLE/DYNAMIC 两个独立 prompt |
| Cards AI | `card_summarizer.py` | SUMMARIZE_SYSTEM_PROMPT |

### 关键原则
- 前端绝不直接调用子 AI，只调 `/chat` 一个端点
- 子 AI 各有独立 API 端点（`/profile/ai/*`、`/cards/ai/*`），可被其他页面直接使用
- Cloudie 的 system prompt 告知它有这些能力，但不包含任何信号/标记规则
- 后台提取用 `asyncio.create_task()` fire-and-forget，不阻塞对话响应

### 主动信号机制
用户明确要求「记下来」「更新档案」时，Cloudie 在回复末尾附加 `<!--PROFILE-->` / `<!--CARD-->` 标记（HTML 注释，用户不可见）。后端 `_parse_signals()` 正则剥离后触发子 AI 服务：
```
Cloudie 回复 "恭喜！<!--CARD--><!--PROFILE-->" 
  → _parse_signals() → clean_reply="恭喜！" + has_card + has_profile
  → 保存 clean_reply 到 DB
  → asyncio.create_task(_handle_signals) → update_dynamic_profile + summarize_to_notes
```

---

## 2026-07-05 — userIdentity 模块加载时序崩溃修复

### 根因
`userIdentity.js` 在模块加载时（import 阶段）就调用了 `userIdentity.init()` → `storage.get()`，此时 app 生命周期尚未开始（`onCreate` 未触发），导致：
1. `storage.get()` 抛异常破坏模块导出 → `app.ux` 中 `userIdentity.init()` 报 `is not a function`
2. Native 报错 "请在 onCreate() 之后调用"

### 修复
- **删除**模块级的 `userIdentity.init()` 自动调用，仅保留 `app.ux onCreate()` 中的调用
- `initUserId()` / `initNickname()` 加缓存守卫（`_userIdPromise` / `_nicknamePromise`），防止多个组件重复调用 storage

### 正确的初始化时序
```
app.ux onCreate() → userIdentity.init() [同步设守卫]
  → initUserId() → storage.get() ✅ (onCreate 已触发)
页面/组件 onInit → await initUserId() → 命中缓存 Promise（不重复调 storage）
```

### ajax.js 关键设计规则
- **Header 注入必须同步**：`getUserId()` 永远有值（eagerUuid fallback），不应阻塞在 `ready()`
- `ready()` 是 fire-and-forget，确保 init 在后台完成，但不阻塞任何请求
- 需要精确 UUID 的页面（如 Family）自己 `await userIdentity.ready()`
- 通用层（ajax.js）不应因身份未就绪而挂起所有 API 调用
