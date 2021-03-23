/**
 * Standard JWT payload fields referenced by `JWT`.
 *
 * See https://tools.ietf.org/html/rfc7519#page-9
 *
 * @typedef JWTPayload
 * @prop {number} exp - Expiration time
 * @prop {number} iat - Issued at
 */

/**
 * Value class for working with JSON Web Tokens [1] issued by the server.
 *
 * [1] https://tools.ietf.org/html/rfc7519
 */
export class JWT {
  /**
   * Construct a JWT to wrap a recently issued JWT token.
   *
   * @param {string} token - Serialized JWT
   * @param {number} issuedAt -
   *   A _client_ timestamp in milliseconds estimating when the JWT was issued.
   *   The estimate should bias towards being earlier than the true time, in
   *   which case the JWT will "expire" earlier than the true expiry.
   */
  constructor(token, issuedAt) {
    this._token = token;

    const [, payloadBase64] = token.split('.');
    this._payload = /** @type {JWTPayload} */ (JSON.parse(atob(payloadBase64)));

    // Estimated offset of server's clock relative to client.
    //
    // +ve if the server's clock is ahead of the client or -ve if the server's
    // clock is behind.
    const skew = this._payload.iat * 1000 - issuedAt;

    this._validUntil = this._payload.exp * 1000 - skew;
  }

  /**
   * Return true if the JWT token has expired.
   *
   * @param {number} [now] - Current timestamp in milliseconds
   */
  hasExpired(now = Date.now()) {
    return now > this._validUntil;
  }

  value() {
    if (this.hasExpired()) {
      throw new Error('Tried to use an expired JWT token');
    }
    return this._token;
  }

  payload() {
    return this._payload;
  }
}
