/**
 * 导出 apis 下目录的所有接口
 * 注意：快应用不支持 require.context，需手动 import
 */

import cards from './cards'
import chat from './chat'
import config from './config'
import profiles from './profiles'
import family from './family'
import chatroom from './chatroom'
import auth from './auth'
import profile_ai from './profile_ai'
import tts from './tts'
import replica from './replica'

export default {
  cards,
  chat,
  config,
  profiles,
  family,
  chatroom,
  auth,
  profile_ai,
  tts,
  replica
}