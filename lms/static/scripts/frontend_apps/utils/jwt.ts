/**
 * Standard JWT payload fields referenced by `JWT`.
 *
 * See https://tools.ietf.org/html/rfc7519#page-9
 */
export type JWTPayload = {
  /** Expiration time. */
  exp: number;

  /** Issued at */
  iat: number;
};

/**
 * Value class for working with JSON Web Tokens [1] issued by the server.
 *
 * [1] https://tools.ietf.org/html/rfc7519
 */
export class JWT {
  private _payload: JWTPayload;
  private _token: string;
  private _validUntil: number;

  /**
   * Construct a JWT to wrap a recently issued JWT token.
   *
   * @param token - Serialized JWT
   * @param issuedAt -
   *   A _client_ timestamp in milliseconds estimating when the JWT was issued.
   *   The estimate should bias towards being earlier than the true time, in
   *   which case the JWT will "expire" earlier than the true expiry.
   */
  constructor(token: string, issuedAt: number) {
    this._token = token;

    try {
      const [, payloadBase64] = token.split('.');
      this._payload = JSON.parse(atob(payloadBase64)) as JWTPayload;
    } catch {
      throw new Error('Failed to parse payload from JWT');
    }

    const iat = this._getField('iat', 'number');
    const exp = this._getField('exp', 'number');

    // Estimated offset of server's clock relative to client.
    //
    // +ve if the server's clock is ahead of the client or -ve if the server's
    // clock is behind.
    const skew = iat * 1000 - issuedAt;
    this._validUntil = exp * 1000 - skew;
  }

  /**
   * Return true if the JWT token has expired.
   *
   * Note that validation for security purposes should be done by the server. Client-side
   * checks of the expiry time are useful to check if a token is expired before
   * it has been used, or if a JWT rejection may have been caused by an expired token.
   *
   * @param [now] - Current timestamp in milliseconds
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

  _getField(field: keyof JWTPayload, type: string) {
    if (typeof this._payload[field] !== type) {
      throw new Error(`Missing or invalid "${field}" field in JWT payload`);
    }
    return this._payload[field];
  }
}
