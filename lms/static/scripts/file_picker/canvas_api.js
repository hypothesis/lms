import Request from 'superagent';

const Constants = {
  GET: 'get',
  POST: 'post',
  DEL: 'del',
  PUT: 'put'
}

export default class CanvasApi {
  constructor() {
    this.baseUrl = window.DEFAULT_SETTINGS.apiUrl;
  }

  proxy(endpointUrl, params = {}) {
    return new Promise((resolve, reject) => {
      Request
      .post(this.baseUrl)
      .send({ method: Constants.GET, endpoint_url: endpointUrl, params })
      .set('Authorization', `Bearer ${window.DEFAULT_SETTINGS.jwt}`)
      .end((err, res) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(res);
      });
    });
  }
}