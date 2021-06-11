import { createElement } from 'preact';

import Table from './Table';

/**
 * @typedef {import('../api-types').Book} Book
 */

/**
 * @typedef BookListProps
 * @prop {Book[]} books - List of available books
 * @prop {boolean} isLoading - Whether to show a loading indicator
 * @prop {Book|null} selectedBook - Book within `books` which is currently selected
 * @prop {(b: Book) => void} onSelectBook - Callback invoked when user selects a book
 * @prop {(b: Book) => void} onUseBook -
 *   Callback invoked when user confirms they want to use the selected book for
 *   an assignment.
 */

/**
 * Component that presents the user with a list of books from a source (eg. VitalSource)
 * and allows them to choose one for an assignment.
 *
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
        items={books}
        isLoading={isLoading}
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
            data-testid="cover-image"
          />
        </div>
      )}
    </div>
  );
}
