/**
 * 聊天室 API —— 家庭组成员互聊
 *
 * 与 chat.js（AI 对话）完全独立。
<<<<<<< HEAD
 */
import $ajax from '../ajax'
import config from './config'
import userIdentity from '../userIdentity'

const baseUrl = config.baseUrl

function uid() {
  return userIdentity.getUserId() || '1'
}

=======
 * user_id 由 ajax.js 自动通过 X-User-Id Header 注入，无需手动传递。
 */
import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

>>>>>>> si
export default {
  /**
   * 获取聊天列表（私聊 + 群聊）
   * @returns {Promise<{conversations: Array}>}
   */
  getConversations() {
<<<<<<< HEAD
    return $ajax.get(`${baseUrl}/chatroom/conversations`, {
      user_id: uid(),
    })
=======
    return $ajax.get(`${baseUrl}/chatroom/conversations`)
>>>>>>> si
  },

  /**
   * 发送消息
   * @param {object} params
   * @param {number|null} params.conversation_id - 已有会话 ID
   * @param {string|null} params.receiver_id - 私聊接收者（新建时必传）
   * @param {string} params.chat_type - "private" | "group"
   * @param {string} params.content - 消息内容
   * @returns {Promise<{conversation_id, message_id, content, created_at}>}
   */
  sendMessage({ conversation_id, receiver_id, chat_type, content }) {
    return $ajax.post(`${baseUrl}/chatroom/send`, {
<<<<<<< HEAD
      user_id: uid(),
=======
>>>>>>> si
      conversation_id: conversation_id || null,
      receiver_id: receiver_id || null,
      chat_type,
      content,
    })
  },

  /**
   * 拉取消息（支持增量轮询）
   * @param {number} conversationId - 会话 ID
   * @param {number} afterId - 只拉取 id > afterId 的消息，0=首次加载
   * @returns {Promise<{conversation_id, messages: Array, has_more: boolean}>}
   */
  getMessages(conversationId, afterId = 0) {
    return $ajax.get(`${baseUrl}/chatroom/messages`, {
      conversation_id: conversationId,
<<<<<<< HEAD
      user_id: uid(),
=======
>>>>>>> si
      after_id: afterId,
      limit: 50,
    })
  },
}
