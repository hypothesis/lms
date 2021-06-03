import { truncateURL } from '../format';

describe('truncateURL', () => {
  [
    // URLs less than the max length are unmodified.
    ['https://example.com', 'https://example.com'],

    // URLs just longer than the max length have their protocol removed.
    ['https://example.com/foobar-bazquux', 'example.com/foobar-bazquux'],

    // URLs that are shorter than the max length after removing the protocol,
    // query string and fragment have those parts removed
    [
      'https://example.com/foobar-bazquux?a-long-query-string#some-fragment',
      'example.com/foobar-bazquux',
    ],

    // URLs that are shorter than the max length after removing some path
    // elements have the path truncated.
    ['https://en.wikipedia.org/wiki/Australia', 'en.wikipedia.org/…/Australia'],

    // URLs that are still too longer after removing all the path elements
    // except the final one are just elided.
    [
      'https://en.wikipedia.org/wiki/Cannonball_Run_challenge',
      'en.wikipedia.org/…/Cannonball…',
    ],
  ].forEach(([input, expected]) => {
    it('truncates a long URL', () => {
      assert.equal(truncateURL(input, 30), expected);
    });
  });

  it('truncates an invalid URL', () => {
    const invalidURL = 'foo$://foobar.com/wibble';
    assert.equal(truncateURL(invalidURL, 10), invalidURL.slice(0, 9) + '…');
  });
});
