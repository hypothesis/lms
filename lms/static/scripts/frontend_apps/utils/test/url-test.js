import { replaceURLParams } from '../url';

describe('replaceURLParams', () => {
  it('should replace params in URLs', () => {
    const replaced = replaceURLParams('https://foo.com/things/:id', {
      id: 'test',
    });
    assert.equal(replaced, 'https://foo.com/things/test');
  });

  it('should replace multiple instances of the same placeholder', () => {
    const replaced = replaceURLParams(
      'https://foo.com/things/:id/more-things/:id',
      {
        id: 'test',
      },
    );
    assert.equal(replaced, 'https://foo.com/things/test/more-things/test');
  });

  it('should URL encode params in URLs', () => {
    const replaced = replaceURLParams('https://foo.com/things/:id', {
      id: 'foo=bar',
    });
    assert.equal(replaced, 'https://foo.com/things/foo%3Dbar');
  });

  it('should throw if some provided params cannot be replaced', () => {
    assert.throws(
      () =>
        replaceURLParams('https://foo.com/:id', {
          id: 'test',
          q: 'unused',
        }),
      'Parameter "q" not found in "https://foo.com/:id" URL template',
    );
  });
});
