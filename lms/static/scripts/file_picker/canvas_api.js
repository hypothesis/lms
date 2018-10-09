import Request from 'superagent';

export const Constants = {
  GET: 'get',
  POST: 'post',
  DEL: 'del',
  PUT: 'put',
  GET_ALL: 'get_all',
};

// Handle the requests to the canvas proxy on the server.
export default class CanvasApi {
  constructor() {
    this.baseUrl = window.DEFAULT_SETTINGS.apiUrl;
  }

  // Proxies requests to the canvas api through the server
  proxy(endpointUrl, method, params = {}) {
    return new Promise((resolve, reject) => {
      // All requests to the proxy are posts.
      Request
        .post(this.baseUrl)
        .send({ endpoint_url: endpointUrl,  method, params })
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
