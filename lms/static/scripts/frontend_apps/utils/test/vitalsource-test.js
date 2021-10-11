import { extractBookID } from '../vitalsource';

describe('extractBookID', () => {
  [
    'https://bookshelf.vitalsource.com/#/books/9781400847402X',

    // It does not matter if there are path elements after the book ID
    'https://bookshelf.vitalsource.com/#/books/9781400847402X/foo/bar',

    // It doesn't matter what the domain is
    'https://whatever.com/#/books/9781400847402X',

    // Trailing slash
    'https://whatever.com/#/books/9781400847402X/',

    // It doesn't even matter if it's a URL
    'whatever/books/9781400847402X/boo',

    // Minimum path variant that will match
    'books/9781400847402X',

    // It should take the first match and ignore other alpha-numeric strings
    // in URL
    'books/9781400847402X/far/out/9781400847402X',
    'books/9781400847402X/far/out/1234567890',
    'books/9781400847402X/far/books/1234567890/ding/dong',

    // Another alphanumeric string earlier in URL should be ignored
    'https://bookshelf.vitalsource.com/1039439489/#/books/9781400847402X/foo/bar',

    '9781400847402X',
  ].forEach(input => {
    it(`should parse book ID from "${input}""`, () => {
      assert.equal(extractBookID(input), '9781400847402X');
    });
  });

  [
    // Lower-case alpha characters do not match
    '9781400847402x',
    // Non-recognized character in string (!)
    '9781400!847402X',
    // `book` is singular
    'https://bookshelf.vitalsource.com/#/book/9781400847402',
    // `/` missing after `books`
    'https://bookshelf.vitalsource.com/#/books9781400847402',
  ].forEach(input => {
    it(`should return null if no book ID found in string "${input}"`, () => {
      assert.isNull(extractBookID(input));
    });
  });
});
