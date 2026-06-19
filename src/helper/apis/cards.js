import $ajax from '../ajax'
import config from './config'

const baseUrl = config.baseUrl

export default {
  list(params) {
    return $ajax.get(`${baseUrl}/cards`, {
      category: params && params.category,
      limit: params && params.limit ? params.limit : 20,
      offset: params && params.offset ? params.offset : 0,
    })
  },
  create(data) {
    return $ajax.post(`${baseUrl}/cards`, data)
  },
  remove(cardId) {
    return $ajax.delete(`${baseUrl}/cards/${cardId}`)
  },
}