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

## 2026-06-20 — 用户档案功能（家庭成员档案 CRUD）

### 需求
在「我的」页面增加「用户档案」功能，支持家庭成员档案的增删改查。档案内容支持 Markdown 格式，前端用 richtext 渲染。

### 架构

```
Profile 页面 → 菜单项「📋 用户档案」→ router.push → ProfileDetail 页面
  → GET /profiles 加载列表（失败降级到本地缓存）
  → POST /profiles 创建
  → PUT /profiles/{id} 更新
  → DELETE /profiles/{id} 删除
```

### 后端改动

#### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/profile.py` | `FamilyMember` ORM：id, name, relation, birth_date, avatar_url, content_md, created_at, updated_at |
| `backend/app/schemas/profile.py` | Pydantic：ProfileCreate, ProfileUpdate, ProfileOut, ProfileListOut |
| `backend/app/api/profile.py` | CRUD 路由：GET/POST/PUT/DELETE `/profiles` |

#### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | +2行：import profile_router + include_router |
| `backend/init_db.py` | +1行：import FamilyMember，确保建表时发现新模型 |

### 前端改动

#### 新增文件

| 文件 | 说明 |
|------|------|
| `src/helper/apis/profiles.js` | API 封装：list/create/update/remove |
| `src/pages/ProfileDetail/index.ux` | 档案列表页：列表展示 + 编辑弹窗 + 详情弹窗（Markdown 渲染） |

#### 修改文件

| 文件 | 改动 |
|------|------|
| `src/manifest.json` | +ProfileDetail 路由 + titleBarText |
| `src/pages/Profile/index.ux` | 菜单列表首位增加「📋 用户档案」入口，点击 router.push 到 ProfileDetail |

### API 新增

| 路由 | 方法 | 功能 |
|------|------|------|
| `/profiles` | GET | 获取全部档案列表 |
| `/profiles` | POST | 创建档案 |
| `/profiles/{id}` | PUT | 更新档案 |
| `/profiles/{id}` | DELETE | 删除档案 |

### 关键设计决策

1. **数据库存储 + Markdown 内容字段**：复用现有 SQLite + SQLAlchemy 体系，content_md 字段存 Markdown 原文
2. **前端 Markdown 渲染**：快应用 `<richtext type="markdown">` 原生支持，无需引入第三方库
3. **本地缓存降级**：列表数据同时缓存到 `@system.storage`，后端不可达时从缓存读取
4. **关系下拉选择**：预设 7 种家庭关系（父亲/母亲/配偶/子女/祖父母/兄弟姐妹/其他家人）
5. **独立页面**：ProfileDetail 作为独立路由页面，编辑体验更好，不影响 Profile 主页结构
