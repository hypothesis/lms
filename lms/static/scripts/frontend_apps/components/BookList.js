import { createElement } from 'preact';

import Table from './Table';

/**
 * @typedef {import('../api-types').Book} Book
 */

/**
 * @typedef BookListProps
 * @prop {Book[]} books
 * @prop {boolean} isLoading
 * @prop {Book|null} selectedBook
 * @prop {(b: Book) => any} onSelectBook
 * @prop {(b: Book) => any} onUseBook
 */

/**
 * @param {BookListProps} props
 */
export default function BookList({
  books,
  isLoading = false,
  selectedBook,
  onSelectBook,
  onUseBook,
}) {
  const columns = [
    {
      label: 'Title',
    },
  ];

  return (
    <div className="BookList">
      <Table
        accessibleLabel="Book list"
        columns={columns}
        contentLoading={isLoading}
        items={books}
        onSelectItem={onSelectBook}
        onUseItem={onUseBook}
        renderItem={book => <td>{book.title}</td>}
        selectedItem={selectedBook}
      />
      {selectedBook && (
        <div className="BookList__cover-container">
          <img
            className="BookList__cover"
            alt="Book cover"
            src={selectedBook.cover_image}
          />
        </div>
      )}
    </div>
  );
}
