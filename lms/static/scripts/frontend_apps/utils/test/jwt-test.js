import { JWT } from '../jwt';

function toBase64(value) {
  return btoa(JSON.stringify(value));
}

function makeToken(payload) {
  const header = {
    alg: 'HS256',
    typ: 'JWT',
  };
  const signature = 'dummysig';
  return `${toBase64(header)}.${toBase64(payload)}.${signature}`;
}

function timestamp() {
  return (Date.now() / 1000) | 0;
}

function expiredJwt() {
  const nbf = timestamp() - 5;
  const token = makeToken({ nbf, exp: nbf + 2 });
  return new JWT(token, nbf * 1000);
}

function validJwt() {
  const nbf = timestamp();
  const token = makeToken({ nbf, exp: nbf + 5 });
  return new JWT(token, Date.now());
}

describe('JWT', () => {
  describe('#payload', () => {
    it('returns parsed payload', () => {
      const payload = { nbf: 100, exp: 500 };
      const token = makeToken(payload);

      const jwt = new JWT(token, 120);

      assert.deepEqual(jwt.payload(), payload);
    });
  });

  describe('#hasExpired', () => {
    [
      {
        // `issuedAt` and `nbf` are equal, so the server and client clocks are
        // assumed to be in-sync.
        issuedAt: 0,
        token: makeToken({ nbf: 0, exp: 5 }),
        now: 2000,
        expired: false,
      },
      {
        // `issuedAt` and `nbf` are equal, so the server and client clocks are
        // assumed to be in-sync.
        issuedAt: 0,
        token: makeToken({ nbf: 0, exp: 5 }),
        now: 7000,
        expired: true,
      },
      {
        // `issuedAt` is behind `nbf`, so the server's clock is assumed to be
        // 1 sec ahead of the client.
        issuedAt: 0,
        token: makeToken({ nbf: 1, exp: 5 }),
        now: 4500,
        expired: true,
      },
      {
        // `issuedAt` is ahead of `nbf`, so the server's clock is assumed to be
        // 1 sec behind the client.
        issuedAt: 1000,
        token: makeToken({ nbf: 0, exp: 5 }),
        now: 5500,
        expired: false,
      },
    ].forEach(({ issuedAt, token, now, expired }) => {
      it('returns true if token has expired', () => {
        const jwt = new JWT(token, issuedAt);
        assert.equal(jwt.hasExpired(now), expired);
      });
    });
  });

  describe('#value', () => {
    it('returns token as a string if valid', () => {
      const jwt = validJwt();
      assert.typeOf(jwt.value(), 'string');
    });

    it('throws an error if token has expired', () => {
      const jwt = expiredJwt();
      assert.throws(() => {
        jwt.value();
      }, 'Tried to use an expired JWT token');
    });
  });
});
