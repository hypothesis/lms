import Request from 'superagent';

export default class CanvasApi {
  constructor(baseUrl) {
    this.baseUrl = window.DEFAULT_SETTINGS.apiUrl;
  }

  proxy(url, params) {
    Request
      .post(`${this.baseUrl}`)
      .send({method: 'get', url, ...params})
      .set('Authorization', window.DEFAULT_SETTINGS.jwt)
  }
}