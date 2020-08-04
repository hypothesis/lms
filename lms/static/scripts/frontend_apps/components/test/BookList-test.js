import { mount } from 'enzyme';
import { createElement } from 'preact';

import BookList from '../BookList';

describe('BookList', () => {
  const bookData = [
    {
      id: 'test-book',
      title: 'Test book',
      cover_image: 'https://example.com/test.jpg',
    },
  ];

  const noop = () => {};
  const renderBookList = (props = {}) =>
    mount(
      <BookList
        books={bookData}
        selectedBook={null}
        onSelectBook={noop}
        onUseBook={noop}
        {...props}
      />
    );

  it('renders book titles', () => {
    const bookList = renderBookList();
    assert.equal(bookList.find('tbody > tr').length, bookData.length);
    assert.include(bookList.html(), '<td>Test book</td>');
  });

  [true, false].forEach(isLoading => {
    it('shows loading indicator if books are being fetched', () => {
      const bookList = renderBookList({ isLoading });
      assert.equal(bookList.find('Table').prop('isLoading'), isLoading);
    });
  });

  it('calls `onSelectBook` callback when a book is selected', () => {
    const onSelectBook = sinon.stub();
    const bookList = renderBookList({ onSelectBook });

    bookList.find('Table').prop('onSelectItem')(bookData[0]);

    assert.calledWith(onSelectBook, bookData[0]);
  });

  it('calls `onUseBook` callback when a book is double-clicked', () => {
    const onUseBook = sinon.stub();
    const bookList = renderBookList({ onUseBook });

    bookList.find('Table').prop('onUseItem')(bookData[0]);

    assert.calledWith(onUseBook, bookData[0]);
  });

  it('does not show a cover image if no book is selected', () => {
    const bookList = renderBookList();
    assert.isFalse(bookList.exists('img[data-testid="cover-image"]'));
  });

  it('shows cover of selected book', () => {
    const bookList = renderBookList({ selectedBook: bookData[0] });
    const coverImage = bookList.find('img[data-testid="cover-image"]');
    assert.equal(coverImage.prop('src'), bookData[0].cover_image);
  });
});
