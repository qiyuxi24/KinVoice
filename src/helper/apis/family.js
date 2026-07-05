/**
 * 家庭组 API
 *
<<<<<<< HEAD
 * 用户身份通过请求体中的 user_id 字段传递（而非 Header），
 * 避免修改现有 ajax.js。
 */
import $ajax from '../ajax'
import config from './config'
import userIdentity from '../userIdentity'

const baseUrl = config.baseUrl

/**
 * 获取当前设备 user_id
 */
function uid() {
  var id = userIdentity.getUserId()
  console.log('[family.js] uid() getUserId=' + JSON.stringify(id) + ' cached=' + JSON.stringify(userIdentity._cachedUserId) + ' final=' + JSON.stringify(id || '1'))
  return id || '1'
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
   * 注册用户（首次使用，设置昵称）
   * @param {string} nickname - 用户昵称
   * @returns {Promise<{user_id, nickname}>}
   */
  register(nickname) {
    return $ajax.post(`${baseUrl}/family/register-with-id`, {
<<<<<<< HEAD
      user_id: uid(),
=======
>>>>>>> si
      nickname,
    })
  },

  /**
   * 创建家庭组
   * @param {string} nickname - 创建者昵称
   * @returns {Promise<{family_id, password, user_id}>}
   */
  createGroup(nickname) {
    return $ajax.post(`${baseUrl}/family/create`, {
<<<<<<< HEAD
      user_id: uid(),
=======
>>>>>>> si
      nickname,
    })
  },

  /**
   * 加入家庭组
   * @param {string} familyId - 8位家庭组ID
   * @param {string} password - 6位数字密码
   * @param {string} nickname - 加入者昵称
   * @returns {Promise<{ok}>}
   */
  joinGroup(familyId, password, nickname) {
    return $ajax.post(`${baseUrl}/family/join`, {
<<<<<<< HEAD
      user_id: uid(),
=======
>>>>>>> si
      family_id: familyId,
      password,
      nickname,
    })
  },

  /**
   * 退出家庭组
   * @returns {Promise<{ok}>}
   */
  leaveGroup() {
<<<<<<< HEAD
    return $ajax.post(`${baseUrl}/family/leave`, {
      user_id: uid(),
    })
=======
    return $ajax.post(`${baseUrl}/family/leave`, {})
>>>>>>> si
  },

  /**
   * 查询我的家庭组
   * @returns {Promise<{family_id, password, members: [{user_id, nickname, joined_at}]}>}
   */
  getMyGroup() {
<<<<<<< HEAD
    return $ajax.get(`${baseUrl}/family/my-group?user_id=${uid()}`)
=======
    return $ajax.get(`${baseUrl}/family/my-group`)
>>>>>>> si
  },
}
