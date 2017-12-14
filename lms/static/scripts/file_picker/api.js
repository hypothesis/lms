import Request from 'superagent';

export default class Api {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  get(url, params) { console.log('called') }
  post(url, params) {}
  put(url, params) {}
  delete(url, params) {}
}