import {
  queryStringToRecord,
  recordToQueryString,
  recordToSearchParams,
  replaceURLParams,
} from '../url';

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

describe('recordToSearchParams', () => {
  it('parses provided record and appends entries', () => {
    const result = recordToSearchParams({
      foo: 'bar',
      baz: ['1', '2', '3'],
      ignored: undefined,
    });

    assert.equal(result.toString(), 'foo=bar&baz=1&baz=2&baz=3');
  });
});

describe('recordToQueryString', () => {
  [
    {
      params: {
        foo: 'bar',
        baz: ['1', '2', '3'],
      },
      expectedResult: '?foo=bar&baz=1&baz=2&baz=3',
    },
    {
      params: {},
      expectedResult: '',
    },
    {
      params: { foo: [], bar: [] },
      expectedResult: '',
    },
  ].forEach(({ params, expectedResult }) => {
    it('parses provided record and appends entries', () => {
      const result = recordToQueryString(params);
      assert.equal(result, expectedResult);
    });
  });
});

describe('queryStringToRecord', () => {
  [
    {
      queryString: '?foo=bar&baz=1&baz=2&baz=3',
      expectedResult: {
        foo: 'bar',
        baz: ['1', '2', '3'],
      },
    },
    {
      queryString: '',
      expectedResult: {},
    },
    {
      queryString: '?',
      expectedResult: {},
    },
  ].forEach(({ queryString, expectedResult }) => {
    it('parses provided record and appends entries', () => {
      const result = queryStringToRecord(queryString);
      assert.deepEqual(result, expectedResult);
    });
  });
});
