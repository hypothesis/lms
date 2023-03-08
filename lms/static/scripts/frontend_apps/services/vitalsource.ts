import type { Book, Chapter } from '../api-types';
import { apiCall, urlPath } from '../utils/api';

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
   * Fetch a list of chapters that can be used as the target location for an
   * ebook assignment.
   *
   * @param bookId - VitalSource book ID ("vbid")
   */
  async fetchChapters(bookId: string): Promise<Chapter[]> {
    return apiCall<Chapter[]>({
      path: urlPath`/api/vitalsource/books/${bookId}/toc`,
      authToken: this._authToken,
    });
  }
}
