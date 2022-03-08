import { toJSTORUrl } from '../jstor';

describe('utils/jstor', () => {
  describe('toJSTORUrl', () => {
    [
      // GOOD URLS
      // URL with article ID
      ['https://www.jstor.org/stable/1234', 'jstor://1234'],
      // Querystring ignored
      ['https://www.jstor.org/stable/1234?q=bananas&bar=baz', 'jstor://1234'],
      // Trailing slash(es) ignored
      ['https://www.jstor.org/stable/1234/', 'jstor://1234'],
      ['https://www.jstor.org/stable/1234//', 'jstor://1234'],
      // http protocol OK
      ['http://www.jstor.org/stable/1234', 'jstor://1234'],
      // DOI Prefx and DOI suffix
      ['https://www.jstor.org/stable/10.1086/508573', 'jstor://10.1086/508573'],
      [
        'https://www.jstor.org/stable/10.1086.3333.9/508573',
        'jstor://10.1086.3333.9/508573',
      ],

      // BAD URLS
      // Not a URL
      ['foo', null],
      // Missing "/stable/"
      ['http://www.jstor.org/1234', null],
      ['https://www.jstor.org/10.1086/508573', null],
      // Bad DOI Prefix format
      ['https://www.jstor.org/stable/10.1086k/508573', null],
      // Bad hostname
      ['https://jstor.org/stable/1234', null],
      // Too many path segments
      ['https://www.jstor.org/stable/10.1086/508573/34434', null],
    ].forEach(([input, expected]) => {
      assert.equal(toJSTORUrl(input), expected);
    });
  });
});
