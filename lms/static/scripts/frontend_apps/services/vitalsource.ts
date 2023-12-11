import type { Book, TableOfContentsEntry } from '../api-types';
import { apiCall, urlPath } from '../utils/api';

/**
 * Range of pages in the book.
 *
 * Page ranges are inclusive, as if the user enters `5-10` they would expect
 * that page 10 is included.
 */
export type PageRange = {
  type: 'page';
  start?: string;
  end?: string;
};

/**
 * Range of entries in the table of contents.
 *
 * CFI ranges are exclusive, so the range includes `start` but not `end`. Since
 * CFIs do not reference predictably-sized chunks of the document (eg. they
 * could refer to a whole chapter, a page or a single paragraph) it is more
 * convenient to treat them as points that refer to the start of a section.
 */
export type TableOfContentsRange = {
  type: 'toc';
  start?: TableOfContentsEntry;
  end?: TableOfContentsEntry;
};

/**
 * Represents a selected range of content in the book.
 *
 * This is expressed as _either_ a page range or a TOC range. Although there is
 * a correspondence between the two, we cannot always represent a selection made
 * using one method in the other form. Therefore whichever method of making a
 * selection is used by the user, that's the canonical representation. Some
 * examples of issues relating the two content range representations:
 *
 *  - Page ranges can start or end in the middle of a chapter
 *  - Chapters can start or end in the middle of a page
 *  - The APIs we use for VitalSource provide only the start page number, not
 *    a page range.
 *  - Although most books use Latin digits for their core content, page numbers
 *    can use other numbering systems (eg. Roman numerals) and mix numbering
 *    systems within the same book.
 */
export type ContentRange = PageRange | TableOfContentsRange;

/**
 * Details of a book and content range selected by the user.
 */
export type Selection = {
  /** Selected book. */
  book: Book;
  content: ContentRange;
};
/**
 * Service for fetching information about available VitalSoure books and the
 * list of chapters in a book.
 */
export class VitalSourceService {
  private _authToken: string;

  constructor({ authToken }: { authToken: string }) {
    this._authToken = authToken;
  }

  /**
   * Fetch metadata about a VitalSource book.
   *
   * @param bookId - VitalSource book ID (aka "vbid")
   */
  async fetchBook(bookId: string): Promise<Book> {
    // Path parameter encoding is currently handled by the `apiCall` caller,
    // but this should be done by `apiCall` in future.
    return apiCall<Book>({
      path: urlPath`/api/vitalsource/books/${bookId}`,
      authToken: this._authToken,
    });
  }

  /**
   * Fetch table of contents for a book.
   *
   * @param bookId - VitalSource book ID ("vbid")
   */
  async fetchTableOfContents(bookId: string): Promise<TableOfContentsEntry[]> {
    return apiCall<TableOfContentsEntry[]>({
      path: urlPath`/api/vitalsource/books/${bookId}/toc`,
      authToken: this._authToken,
    });
  }

  /**
   * Translate a book and content selection to a document URL for an assignment.
   *
   * @param selection - The book and content selection
   */
  async fetchDocumentURL(selection: Selection): Promise<string> {
    const { book, content } = selection;
    const params: Record<string, string> = {};
    if (content.type === 'toc' && content.start) {
      params.cfi = content.start.cfi;
      if (content.end) {
        params.end_cfi = content.end.cfi;
      }
    }
    if (content.type === 'page' && content.start) {
      params.page = content.start;
      if (content.end) {
        params.end_page = content.end;
      }
    }

    type DocumentURLResponse = {
      document_url: string;
    };

    const response = await apiCall<DocumentURLResponse>({
      authToken: this._authToken,
      path: '/api/vitalsource/document_url',
      params: {
        book_id: book.id,
        ...params,
      },
    });

    return response.document_url;
  }
}
