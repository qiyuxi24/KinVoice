/**
 * 导出 apis 下目录的所有接口
 * 注意：快应用不支持 require.context，需手动 import
 */
import auth from './auth'
import cards from './cards'
import chat from './chat'
import chatroom from './chatroom'
import config from './config'
import family from './family'
import profiles from './profiles'

export default { auth, cards, chat, chatroom, config, family, profiles }
