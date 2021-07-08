import { bookIDFromURL } from '../vitalsource';

describe('bookIDFromURL', () => {
  [
    'https://bookshelf.vitalsource.com/#/books/9781400847402',

    // It does not matter if there are path elements after the book ID
    'https://bookshelf.vitalsource.com/#/books/9781400847402/foo/bar',

    // It doesn't matter what the domain is
    'https://whatever.com/#/books/9781400847402',

    // It doesn't even matter if it's a URL
    'whatever/books/9781400847402/boo',

    // Minimum thing that will match
    'books/9781400847402',
  ].forEach(url => {
    it('should parse book ID from URL', () => {
      assert.equal(bookIDFromURL(url), '9781400847402');
    });
  });

  [
    // `book` is singular
    'https://bookshelf.vitalsource.com/#/book/9781400847402',

    // missing slash in path
    'https://bookshelf.vitalsource.com/#/books9781400847402',

    // vbid by itself (at some point we might want to accept this),
    '9781400847402',

    // Non-matching character '!' in ID
    'https://bookshelf.vitalsource.com/#/books/9781400!847402',

    // Missing 'books' path element
    'https://bookshelf.vitalsource.com/#/9781400847402',
  ].forEach(url => {
    it('should return `null` if no book ID found in string', () => {
      assert.equal(bookIDFromURL(url), null);
    });
  });
});
