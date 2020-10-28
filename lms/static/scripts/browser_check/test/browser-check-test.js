import { isBrowserSupported } from '../browser-check';

describe('isBrowserSupported', () => {
  it('returns true in a modern browser', () => {
    assert.isTrue(isBrowserSupported());
  });

  it('returns false if a check fails', () => {
    const stub = sinon
      .stub(Promise, 'resolve')
      .throws(new Error('Not supported'));

    assert.isFalse(isBrowserSupported());

    stub.restore();
  });
});
