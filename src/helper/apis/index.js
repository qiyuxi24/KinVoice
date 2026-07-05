/**
 * 导出 apis 下目录的所有接口
 * 注意：快应用不支持 require.context，需手动 import
 */
import cards from './cards'
import chat from './chat'
import config from './config'
import profiles from './profiles'

export default { cards, chat, config, profiles }