# KinVoice — 家庭沟通智能助手

> 前端：快应用（Quick App） | 后端：FastAPI + SQLite | AI：LLM 大模型  
> 通过 AI 陪伴对话、家庭组、传承笔记、语音合成，促进家庭成员间的沟通与记忆传承。

---

## 一、项目结构

```
KinVoice/
├── src/                         # ★ 快应用前端源码
│   ├── app.ux                   # 入口：全局注入 $utils/$apis/$user，触发身份初始化
│   ├── manifest.json            # 应用配置 + 路由表
│   ├── assets/
│   │   └── styles/              # variables.less, mixins.less, style.less
│   ├── pages/
│   │   ├── Main/                # 单页容器（if 指令切换 4 个 Tab 组件）
│   │   ├── ProfileDetail/       # 用户档案详情（Markdown 阅读/编辑）
│   │   ├── Family/              # 家庭组管理（创建/加入/成员列表）
│   │   ├── FamilyJoin/          # 加入家庭组（输入 ID + 密码）
│   │   ├── ChatRoom/            # 家庭聊天室（私聊/群聊，轮询消息）
│   │   ├── BreakIce/            # 破冰页（独立页，家庭聊天入口）
│   │   └── About/               # 关于页面
│   ├── components/
│   │   ├── CompanionTab/        # Tab 1：Cloudie AI 陪伴对话
│   │   ├── BreakIceTab/         # Tab 2：破冰页入口
│   │   ├── MemoryTab/           # Tab 3：传承笔记（文件夹 + 笔记 CRUD）
│   │   ├── ProfileTab/          # Tab 4：我的（头像/昵称/菜单）
│   │   └── Tabbar/              # 底部 TabBar（事件驱动切换）
│   ├── helper/
│   │   ├── ajax.js              # 网络层：Promise 封装 @system.fetch（超时 20s）
│   │   ├── userIdentity.js      # 用户身份：设备 UUID + 昵称（storage 持久化）
│   │   ├── utils.js             # 工具方法（showToast, queryString 等）
│   │   ├── navigate.js          # 路由封装（safePush/safeBack）
│   │   ├── errorCodes.js        # 错误码体系
│   │   └── apis/                # 业务接口层
│   │       ├── config.js        # baseUrl 配置
│   │       ├── chat.js          # /chat 对话
│   │       ├── cards.js         # /folders, /cards 笔记
│   │       ├── profiles.js      # /profiles 档案
│   │       ├── family.js        # /family 家庭组
│   │       ├── chatroom.js      # /chatroom 聊天室
│   │       └── index.js         # 聚合导出到 $apis
│   └── CardDemo/                # 快应用卡片示例（厂商专属）
│
├── backend/                     # ★ FastAPI 后端
│   ├── start.py                 # 一键启动脚本
│   ├── init_db.py               # 建表 + 迁移脚本
│   ├── .env / .env.example      # LLM_API_KEY 等环境变量
│   ├── data/kinvoice.db         # SQLite 数据库
│   └── app/
│       ├── main.py              # FastAPI 入口（11 个路由 + CORS + 异常处理）
│       ├── config.py            # Pydantic Settings 配置管理
│       ├── api/                 # 路由层
│       │   ├── chat.py          # POST /chat — Cloudie 陪伴对话（核心）
│       │   ├── memory.py        # CRUD /folders, /cards — 传承笔记
│       │   ├── summarize.py     # POST /chat/summarize — 对话总结
│       │   ├── profile.py       # CRUD /profiles — 用户档案
│       │   ├── profile_ai.py    # /profile/ai — AI 档案编写
│       │   ├── cards_ai.py      # /cards/ai — AI 卡片提取
│       │   ├── family.py        # /family — 家庭组管理
│       │   ├── chatroom.py      # /chatroom — 家庭聊天室
│       │   ├── tts.py           # /tts — 文本转语音
│       │   └── replica.py       # /replica — 音色克隆
│       ├── services/            # 业务逻辑层
│       │   ├── llm_service.py   # LLM 调用封装（兼容 OpenAI 接口）
│       │   ├── cloudie_prompt.py # Cloudie 系统提示词工程
│       │   ├── profile_writer.py # AI 档案编写服务
│       │   ├── card_summarizer.py # 对话→传承笔记提取
│       │   ├── search_service.py  # FTS5 全文检索
│       │   ├── family_service.py  # 家庭组业务逻辑
│       │   ├── tts_service.py     # TTS 语音合成
│       │   └── replica_service.py # 音色克隆服务
│       ├── models/              # ORM 数据模型
│       │   ├── card.py          # Conversation + ChatMessage + Card + Folder
│       │   └── profile.py       # FamilyMember（用户档案）
│       ├── schemas/             # Pydantic 请求/响应模型
│       ├── middleware/
│       │   └── user_identity.py # X-User-Id 提取中间件
│       ├── db/
│       │   └── session.py       # 异步 SQLAlchemy 引擎 + Session
│       └── utils/
│           └── logger.py        # loguru 日志配置
│
├── scripts/                     # 前端辅助脚本
├── DEBT.md                      # 技术债务 + 常见错误排查
├── env-requirement.md           # 环境要求
└── package.json                 # 前端依赖
```

---

## 二、核心功能

### 2.1 Cloudie AI 陪伴对话

主 Tab，AI 温暖陪伴者。后端 chat.py 自动编排：
- 每次对话注入用户档案 + FTS5 全文检索上下文
- 对话结束后 fire-and-forget 后台提取档案更新 + 传承卡片
- 支持主动标记 `<!--PROFILE-->` / `<!--CARD-->` 触发即时保存

```
用户输入 → POST /chat → 注入档案 + 检索上下文 → LLM 回复
                                    └→ 后台：更新档案 / 提取卡片
```

### 2.2 家庭组

创建/加入家庭组（8 位 ID + 6 位密码），成员管理。

| 接口 | 功能 |
|------|------|
| POST `/family/create` | 创建家庭组 |
| POST `/family/join` | 加入家庭组 |
| GET `/family/my-group` | 查询我的家庭组 |
| POST `/family/leave` | 退出家庭组 |

### 2.3 家庭聊天室

私聊 + 群聊，轮询增量拉取消息。

| 接口 | 功能 |
|------|------|
| POST `/chatroom/send` | 发送消息 |
| GET `/chatroom/messages` | 增量拉取（after_id 轮询） |
| GET `/chatroom/conversations` | 聊天列表 |

### 2.4 传承笔记

文件夹 + Markdown 笔记 CRUD，支持长按移动、编辑、删除。

| 接口 | 功能 |
|------|------|
| CRUD `/folders` | 文件夹管理 |
| CRUD `/cards` | 笔记增删改查 |
| POST `/chat/summarize` | AI 从对话中自动总结笔记 |

### 2.5 用户档案

每用户一份 Markdown 档案，阅读/编辑双模式。  
Cloudie 对话中可自然语言更新档案（后台 AI 提取）。

| 接口 | 功能 |
|------|------|
| GET `/profiles/mine` | 获取我的档案 |
| POST/PUT/DELETE `/profiles` | 创建/更新/删除 |
| POST `/profile/ai/extract` | AI 从对话更新档案 |

### 2.6 TTS 语音 + 音色克隆

文本转语音（8 种系统音色 + 自定义音色），支持声音复刻。

| 接口 | 功能 |
|------|------|
| POST `/tts` | 文本→WAV 音频 |
| GET `/tts/voices` | 可用音色列表 |
| POST `/replica/create` | 上传录音创建音色 |
| GET `/replica/list` | 自定义音色列表 |

---

## 三、前端架构

### 3.1 单页容器 + Tab 组件

4 个 Tab 通过 MainPage 容器 + `if` 指令切换，Tabbar 用 `$dispatch('tabchange')` 事件驱动。  
每个 Tab 组件通过 `if` 指令控制创建/销毁，`onInit` 时重置数据 + 加载。

```
MainPage
  ├─ if tab === 'companion' → CompanionTab
  ├─ if tab === 'breakice'   → BreakIceTab
  ├─ if tab === 'memory'     → MemoryTab
  └─ if tab === 'profile'    → ProfileTab
```

### 3.2 通信架构

```
页面/组件
  → $apis.xxx.method()          # 业务接口层
    → $ajax.get/post/put/delete()  # 网络封装层
      → @system.fetch               # 快应用原生
        → HTTP → FastAPI 后端
```

### 3.3 用户身份

`userIdentity.js` 管理设备 UUID + 昵称：
- 模块加载时生成 `eagerUuid`，确保 `getUserId()` 永远有值
- `app.ux onCreate()` 触发 `init()` → 从 storage 恢复 UUID + 昵称
- 所有 API 请求自动注入 `X-User-Id` Header
- 未注册用户点击头像即可设置昵称完成登录

### 3.4 前端 API 接口

| 调用方式 | HTTP | 说明 |
|---------|------|------|
| `$apis.chat.sendMessage({message, history})` | POST `/chat` | 陪伴对话 |
| `$apis.cards.list({folder_id?, limit?})` | GET `/cards` | 笔记列表 |
| `$apis.cards.create({title, content, folder_id?})` | POST `/cards` | 创建笔记 |
| `$apis.cards.update(id, data)` | PUT `/cards/{id}` | 更新笔记 |
| `$apis.cards.remove(id)` | DELETE `/cards/{id}` | 删除笔记 |
| `$apis.folders.list()` | GET `/folders` | 文件夹列表 |
| `$apis.folders.create({name})` | POST `/folders` | 创建文件夹 |
| `$apis.profiles.mine()` | GET `/profiles/mine` | 获取我的档案 |
| `$apis.profiles.create({content_md})` | POST `/profiles` | 创建档案 |
| `$apis.profiles.update(id, data)` | PUT `/profiles/{id}` | 更新档案 |
| `$apis.family.create({nickname})` | POST `/family/create` | 创建家庭组 |
| `$apis.family.join({family_id, password})` | POST `/family/join` | 加入家庭组 |
| `$apis.family.getMyGroup()` | GET `/family/my-group` | 查询家庭组 |
| `$apis.chatroom.send({conversation_id, message})` | POST `/chatroom/send` | 发送消息 |
| `$apis.chatroom.getMessages({conversation_id, after_id})` | GET `/chatroom/messages` | 拉取消息 |

---

## 四、后端架构

### 4.1 技术栈

| 组件 | 用途 |
|------|------|
| FastAPI 0.115 | Web 框架 |
| SQLAlchemy 2.0（异步） | ORM |
| aiosqlite | SQLite 异步驱动 |
| httpx | LLM API 调用 |
| Pydantic 2.7 | 数据校验 |
| loguru | 日志 |

### 4.2 数据模型

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  family_members  │     │   conversations   │     │     cards       │
│─────────────────│     │──────────────────│     │─────────────────│
│ id (PK)         │     │ id (PK)           │     │ id (PK)         │
│ user_id         │     │ title             │     │ title           │
│ name            │     │ user_id           │     │ content (MD)    │
│ content_md      │     │ family_id         │     │ author          │
│ relation        │     │ type (ai/private  │     │ folder_id (FK)  │
│ birth_date      │     │        /group)     │     │ family_id       │
│ created_at      │     │ created_at        │     │ created_at      │
│ updated_at      │     └───────┬──────────┘     │ updated_at      │
└─────────────────┘             │                 └────────┬────────┘
                                │ 1:N                      │ N:1
                                ▼                          ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │  chat_messages    │     │    folders      │
                    │──────────────────│     │─────────────────│
                    │ id (PK)          │     │ id (PK)         │
                    │ conversation_id  │     │ name            │
                    │ role / sender_id │     │ family_id       │
                    │ content          │     │ created_at      │
                    │ created_at       │     └─────────────────┘
                    └──────────────────┘
```

### 4.3 路由注册（main.py）

```
/               → 健康检查
/chat           → Cloudie 陪伴对话
/chat/summarize → 对话总结
/folders        → 文件夹 CRUD
/cards          → 笔记 CRUD
/cards/ai       → AI 卡片提取
/profiles       → 用户档案 CRUD
/profile/ai     → AI 档案编写
/family         → 家庭组管理
/chatroom       → 聊天室
/tts            → 文本转语音
/replica        → 音色克隆
```

---

## 五、环境变量

后端 `.env` 配置：

| 变量 | 说明 | 必填 |
|------|------|------|
| `LLM_API_KEY` | LLM 接口密钥 | 是 |
| `LLM_API_BASE` | LLM 接口地址 | 是 |
| `LLM_MODEL` | 模型名称 | 否（默认 qwen-plus） |
| `DATABASE_URL` | 数据库连接 | 否（默认 SQLite） |
| `LOG_LEVEL` | 日志级别 | 否（默认 INFO） |
| `TTS_APP_ID` | vivo TTS App ID | 否 |
| `TTS_APP_KEY` | vivo TTS App Key | 否 |

前端 `src/helper/apis/config.js`：`baseUrl` 指向后端地址。

---

## 六、启动

### 后端

```bash
cd backend
cp .env.example .env        # 编辑填入 LLM_API_KEY
python init_db.py           # 初始化数据库
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
npm install                 # 安装依赖
npm run start               # hap server --watch（模拟器预览）
npm run build               # 编译 rpk 包
```

模拟器预览时前端默认请求 `http://localhost:8000`。真机调试需将 `config.js` 中的 `baseUrl` 改为电脑局域网 IP。

---

## 七、设计原则

- **单页容器**：4 个 Tab 共用 MainPage，避免页面频繁销毁重建
- **解耦优先**：AI 服务（Cloudie / Profile / Cards）各有独立 prompt + API，chat.py 统一编排
- **身份透明**：设备 UUID 自动管理，用户无感知；昵称即登录
- **渐进增强**：前端离线降级，后端 Mock 兜底，不阻塞核心体验
- **组件化**：Tab 组件通过 `data:` + `if` 指令控制生命周期
