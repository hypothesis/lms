import { articleIdFromUserInput } from '../jstor';

describe('utils/jstor', () => {
  describe('articleIdFromUserInput', () => {
    [
      // Plain article ID
      ['1234', '1234'],
      ['j.ctv125jfg.3.6', 'j.ctv125jfg.3.6'],

      // DOI
      ['10.2307/1234', '10.2307/1234'],
      ['10.7591/j.ctt5hh13f.4', '10.7591/j.ctt5hh13f.4'],

      // URL with article ID
      ['https://www.jstor.org/stable/1234', '1234'],

      // Querystring ignored
      ['https://www.jstor.org/stable/1234?q=bananas&bar=baz', '1234'],

      // Trailing slash(es) ignored
      ['https://www.jstor.org/stable/1234/', '1234'],
      ['https://www.jstor.org/stable/1234//', '1234'],

      // http protocol OK
      ['http://www.jstor.org/stable/1234', '1234'],

      // DOI Prefx and DOI suffix
      ['https://www.jstor.org/stable/10.1086/508573', '10.1086/508573'],
      [
        'https://www.jstor.org/stable/10.1086.3333.9/508573',
        '10.1086.3333.9/508573',
      ],

      // PDF URLs
      ['https://www.jstor.org/stable/pdf/4101611.pdf', '4101611'],
      [
        'https://www.jstor.org/stable/pdf/10.7591/j.ctt5hh13f.4.pdf',
        '10.7591/j.ctt5hh13f.4',
      ],

      // Proxied JSTOR URLs
      ['https://www-jstor-org.someuni.edu/stable/1234', '1234'],
      ['https://www.jstor.org.someproxy.usc.edu/stable/1234', '1234'],
      [
        'https://www.jstor.org.someproxy.usc.edu/stable/pdf/abc.def.pdf',
        'abc.def',
      ],
    ].forEach(([input, expected]) => {
      it('returns article ID if input format is supported', () => {
        assert.equal(articleIdFromUserInput(input), expected);
      });
    });

    [
      // Not a URL or ID
      'foo-bar',

      // Missing "/stable/"
      'http://www.jstor.org/1234',
      'https://www.jstor.org/10.1086/508573',

      // Bad DOI Prefix format
      'https://www.jstor.org/stable/10.1086k/508573',

      // Bad hostname
      'https://othersite.org/stable/1234',
      'https://daily.jstor.org/stable/1234',
      'https://not-jstor.com.someproxy.edu/stable/1234',

      // Too many path segments
      'https://www.jstor.org/stable/10.1086/508573/34434',
    ].forEach(input => {
      it('returns null if article ID cannot be extracted', () => {
        assert.isNull(articleIdFromUserInput(input));
      });
    });
  });
});
