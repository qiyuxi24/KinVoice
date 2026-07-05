# 技术债务清单

> 生成日期：2026-07-04  
> 用于追踪项目中已知的冗余代码、设计问题和待优化项，统一管理，分批清理。

---

## 🔴 高优先级（影响功能正确性 / 运行成本）

### 1. Companion.onHide() 触发两次 LLM 调用

**位置**：`src/pages/Companion/index.ux` → `onHide()` + 早期可能存在的 summarize 调用

**问题**：离开 Companion 页面时，可能同时触发：
- `POST /chat/summarize`（提取 NVC 经验卡片）
- `POST /profile/ai/update-dynamic`（更新动态用户档案）

每次都是独立的千问 API 调用，token 消耗翻倍。

**建议方案**：合并为一次调用，让 LLM 同时返回卡片 + 档案更新；或将 summarize 改为可选/手动触发。

**影响**：API 费用 + 响应延迟

---

### 2. Card 模型三种语义混在一张表（上帝表）

**位置**：`backend/app/models/card.py` → `Card` 类，`backend/app/api/memory.py`

**问题**：`cards` 表通过 `type` 字段承载三种不同语义：

| type | 语义 | 使用字段 |
|------|------|----------|
| `"nvc"` | NVC 四要素经验卡片 | `category`, `emotion`, `observation`, `feeling`, `need`, `request` |
| `"chat_message"` | 收藏的单条 AI 回复 | `conversation_id`, `message_id`, `title`, `content`, `original_text` |
| `"chat_conversation"` | 收藏的整个对话 | 定义了但**从未实际使用** |

**具体问题**：
- `observation` 在 NVC 中是"观察事实"，在同步逻辑 (`memory.py:sync_cards`) 中被映射为 `title`，语义不一致
- `feeling` 在 NVC 中是"感受"，在同步中被映射为 `content`
- `type="chat_conversation"` 没有任何代码创建此类型的卡片
- `Conversation.is_favorited` 和 `ChatMessage.is_favorited` 字段定义了但从未被写入
- `Card.to_dict()` 方法定义了但项目中没有任何地方调用（序列化都走 Pydantic）

**建议方案**：拆分为三张表（`nvc_cards` / `favorite_messages` / `favorite_conversations`）或使用 SQLAlchemy 单表继承。至少用 Pydantic discriminated union 做运行时类型区分。

**影响**：维护隐患，字段映射不一致容易出 bug

---

### 3. POST /cards/favorite 后端完整但前端未接入

**位置**：`backend/app/api/memory.py` → `POST /cards/favorite`，`src/helper/apis/cards.js`

**问题**：
- 后端完整实现了 `favorite_conversation()` 函数，包含消息获取、卡片创建、关键词去重
- `src/helper/errorCodes.js` 中有对应错误码（3036/3037/3038）
- 但前端 `cards.js` 没有 `favorite()` 方法，没有任何页面调用此接口

**建议方案**：确认是否需要此功能。需要则补前端接入，不需要则删除后端代码。

**影响**：白写的代码，增加维护负担

---

## 🟡 中优先级（死代码 / 未使用）

### 4. chat_conversation 卡片类型从未使用

**位置**：`backend/app/models/card.py` → `Card.type`

**问题**：`type` 字段的注释和 `memory.py` 中提到了 `"chat_conversation"` 类型（收藏整个对话），但：
- `POST /cards/favorite` 只创建 `type="chat_message"`
- 没有任何地方创建 `type="chat_conversation"`
- `Conversation.is_favorited` 字段从未被设为 `True`

**建议方案**：如果不需要整个对话收藏功能，删除 `chat_conversation` 类型和 `is_favorited` 字段。

---

### 5. llm_service 中未使用的函数

**位置**：`backend/app/services/llm_service.py`

**问题**：
- `chat()` 函数（第 77 行）：对 `call_llm()` 的简单包装，添加了超时/异常处理。但 `chat.py` API 路由直接调用 `call_llm()` 和 `chat_with_system()`，**`chat()` 从未被使用**。
- `chat_completion()` 函数（第 98 行）：是 `call_llm()` 的直接透传（忽略 temperature/max_tokens 参数），**未被使用**。

**建议方案**：删除 `chat()` 和 `chat_completion()`，或标记 deprecated。

---

### 6. Demo / DemoDetail 框架模板页面

**位置**：`src/pages/Demo/index.ux`，`src/pages/DemoDetail/index.ux`

**问题**：快应用框架自带的示例模板页面，与 KinVoice 业务完全无关。路由中已注册但无任何导航入口指向它们。

**建议方案**：删除两个页面文件，从 `manifest.json` 中移除路由注册。

**影响**：无功能影响，纯粹是死代码

---

### 7. ~~apis/index.js 遗漏 profile_ai 导出~~ ✅ 已删除（profile_ai 模块已整体移除）

**位置**：`src/helper/apis/index.js`

**状态**：profile_ai 手动触发机制已被对话中自动触发取代，整个模块已删除，本条作废。

---

### 8. POST /chat 的 si 兼容分支

**位置**：`backend/app/api/chat.py` → `chat_endpoint()` 第 60-72 行

**问题**：当请求显式传 `history` 且 `conversation_id=None` 时，走无状态模式（`chat_with_system`）。当前前端 `chat.js` 只传 `message` + `conversation_id`，不会触发此分支。仅作为旧前端过渡期兼容保留。

**建议方案**：标记为 deprecated，如果确认旧前端已不再使用则可删除。

---

## 🟢 低优先级（优化建议）

### 9. sync_cards 硬编码 type="nvc"

**位置**：`backend/app/api/memory.py` → `sync_cards()` 第 183 行

**问题**：同步逻辑始终创建 `type="nvc"` 的卡片，不处理对话收藏类型。如果未来 Card 模型拆分，这里需要同步修改。

---

### 10. cloudie_prompt.py 与 llm_service.py 两套系统提示词

**位置**：`backend/app/services/cloudie_prompt.py`，`backend/app/services/llm_service.py`

**问题**：`CLOUDIE_SYSTEM_PROMPT`（温暖陪伴）和 `SYSTEM_PROMPT_CHAT`（NVC 倾听）是两套不同的提示词，分别用于 xia 模式和 si 兼容模式。这是有意为之，不算重复，但可以考虑统一管理所有 prompt 到一个文件。

---

### 11. family_members 表命名冲突

**位置**：`backend/app/models/profile.py` → `FamilyMember`，`backend/app/models/family.py` → `FamilyMembership`

**问题**：现有 `family_members` 表是"家庭成员档案"（父亲/母亲的名字、生日），新增的 `family_memberships` 表是"家庭组成员关系"。两者概念不同但命名容易混淆。

**建议方案**：将现有 `family_members` 重命名为 `family_member_profiles`，或在注释中明确区分。

---

## 📋 清理计划

| 批次 | 条目 | 预计工作量 |
|------|------|-----------|
| 第一批 | #1 合并 onHide LLM 调用 | 小 |
| 第一批 | #3 favorite 接口清理 | 小 |
| 第一批 | #5 删除未用函数 | 小 |
| 第一批 | #6 删除 Demo 页面 | 小 |
| 第一批 | ~~#7 补 profile_ai 导出~~ ✅ | - |
| 第二批 | #4 chat_conversation 清理 | 中 |
| 第二批 | #8 si 兼容分支标记 | 小 |
| 第三批 | #2 Card 模型拆分 | **大** |
| 第三批 | #9 sync_cards 重构 | 中 |
