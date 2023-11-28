import { Button, Input, ModalDialog } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useMemo, useEffect, useState } from 'preact/hooks';

import type { Book, TableOfContentsEntry } from '../api-types';
import { useService, VitalSourceService } from '../services';
import type { ContentRange, Selection } from '../services/vitalsource';
import { isPageRangeValid } from '../utils/vitalsource';
import BookSelector from './BookSelector';
import ErrorDisplay from './ErrorDisplay';
import TableOfContentsPicker from './TableOfContentsPicker';

export type BookPickerProps = {
  /**
   * Whether the user can select a range of pages for the assignment, as opposed
   * to just a start point.
   */
  allowPageRangeSelection?: boolean;

  onCancel: () => void;

  /**
   * Callback invoked when both a book and chapter have been selected.
   *
   * @param selection - The content selected by the user
   * @param documentURL - The corresponding document URL for use as the
   *   assignment's document URL
   */
  onSelectBook: (selection: Selection, documentURL: string) => void;
};

type PageRangePickerProps = {
  /** Current start of page range. */
  start?: string;

  /** Current end of page range. */
  end?: string;

  /**
   * Indicates the start page that corresponds to the table of contents
   * selection.
   */
  startPlaceholder?: string;

  /**
   * Indicates the approximate end page that corresponds to the table of
   * contents selection. This is approximate because we don't have enough
   * information to be certain of the exact end page.
   */
  endPlaceholder?: string;

  onChangeStart?: (start: string) => void;
  onChangeEnd?: (end: string) => void;
};

function PageRangePicker({
  start,
  startPlaceholder,
  end,
  endPlaceholder,
  onChangeStart,
  onChangeEnd,
}: PageRangePickerProps) {
  return (
    <div className="font-bold" data-testid="page-range">
      From page{' '}
      <Input
        aria-label="Start page"
        classes="!w-16" // Override `w-full` default
        data-testid="start-page"
        placeholder={startPlaceholder}
        value={start}
        onInput={e =>
          onChangeStart?.((e.target as HTMLInputElement).value.trim())
        }
      />{' '}
      to{' '}
      <Input
        aria-label="End page"
        classes="!w-16" // Override `w-full` default
        data-testid="end-page"
        placeholder={endPlaceholder}
        value={end}
        onInput={e =>
          onChangeEnd?.((e.target as HTMLInputElement).value.trim())
        }
      />
    </div>
  );
}

/**
 * A dialog that allows the user to select a book and chapter to use in an assignment.
 *
 * The list of available books is fetched from VitalSource, but this component
 * could be adapted to work with other book sources in future.
 *
 * The dialog has two steps: The user first chooses a book to use and then chooses
 * which chapter to use from that book. Once both are chosen the `onSelectBook`
 * callback is called.
 */
export default function BookPicker({
  allowPageRangeSelection = false,
  onCancel,
  onSelectBook,
}: BookPickerProps) {
  const vsService = useService(VitalSourceService);

  const [tableOfContents, setTableOfContents] = useState<
    TableOfContentsEntry[] | null
  >(null);
  const [book, setBook] = useState<Book | null>(null);

  const [contentRange, setContentRange] = useState<ContentRange>();

  const [step, setStep] = useState<'select-book' | 'select-toc'>('select-book');
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const confirmBook = useCallback((book: Book) => {
    setBook(book);
    setTableOfContents(null);
    setStep('select-toc');
  }, []);

  const confirmChapter = useCallback(
    async (entry?: TableOfContentsEntry) => {
      /* istanbul ignore next - early exit should be unreachable */
      if (!contentRange) {
        return;
      }
      const selection: Selection = {
        book: book!,
        content: entry ? { type: 'toc', start: entry } : contentRange,
      };
      try {
        setLoading(true);
        const documentURL = await vsService.fetchDocumentURL(selection);
        onSelectBook(selection, documentURL);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    },
    [book, contentRange, onSelectBook, vsService]
  );

  const updatePageRange = (start: string, end: string) => {
    setContentRange({ type: 'page', start, end });
  };
  const pageRange = contentRange?.type === 'page' ? contentRange : undefined;
  const tocEntry =
    (contentRange?.type === 'toc' ? contentRange.start : null) ?? null;

  useEffect(() => {
    if (step === 'select-toc' && !tableOfContents) {
      const currentBook = book!;
      vsService
        .fetchTableOfContents(currentBook.id)
        .then(setTableOfContents)
        .catch(setError);
    }
  }, [book, step, tableOfContents, vsService]);

  const validContentRange =
    contentRange?.type === 'toc' ||
    (contentRange?.type === 'page' &&
      isPageRangeValid(contentRange.start ?? '', contentRange.end ?? ''));

  // Compute the page number that corresponds to the currently selected
  // table-of-contents entry. This cannot always be determined and can be
  // incorrect or off-by-one, due to limitations of the data from the API,
  // so should only used as a hint.
  const endPageForTOCRange = useMemo(() => {
    if (!tableOfContents || !tocEntry) {
      return '';
    }
    const idx = tableOfContents.indexOf(tocEntry);
    const level = tocEntry.level ?? 0;
    let endPage = tocEntry.page;
    for (let i = idx + 1; i < tableOfContents.length; i++) {
      const entryLevel = tableOfContents[i].level ?? 0;
      if (entryLevel <= level) {
        endPage = tableOfContents[i].page;
        break;
      }
    }
    return endPage;
  }, [tableOfContents, tocEntry]);

  const canSubmit =
    (step === 'select-book' && book) ||
    (step === 'select-toc' && validContentRange);

  const pageRangeHeading = allowPageRangeSelection
    ? 'Choose chapter or page range'
    : 'Pick where to start reading';

  return (
    <ModalDialog
      classes={classnames(
        // Set a fix height when selecting a chapter so the modal content
        // doesn't resize after loading.
        { 'h-[25rem]': step === 'select-toc' }
      )}
      // Opt out of Modal's automatic focus handling; route focus manually in
      // sub-components
      initialFocus={'manual'}
      onClose={onCancel}
      scrollable={false}
      title={
        step === 'select-book'
          ? 'Paste link to VitalSource book'
          : pageRangeHeading
      }
      size="lg"
      buttons={
        <>
          {allowPageRangeSelection && step === 'select-toc' && (
            <>
              <PageRangePicker
                start={pageRange?.start ?? ''}
                startPlaceholder={tocEntry?.page}
                end={pageRange?.end ?? ''}
                endPlaceholder={endPageForTOCRange}
                onChangeStart={start =>
                  updatePageRange(start, pageRange?.end ?? '')
                }
                onChangeEnd={end =>
                  updatePageRange(pageRange?.start ?? '', end)
                }
              />
              <div className="flex-grow" />
            </>
          )}
          <Button data-testid="cancel-button" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            key="submit"
            data-testid="select-button"
            disabled={!canSubmit || loading}
            onClick={() => {
              // nb. The `book` and `chapter` checks should be redundant, as the button
              // should not be clickable if no book/chapter is selected, but they
              // keep TS happy.
              if (step === 'select-book' && book) {
                confirmBook(book);
              } else if (step === 'select-toc' && contentRange) {
                confirmChapter();
              }
            }}
            variant="primary"
          >
            {step === 'select-book' ? 'Select book' : 'Select'}
          </Button>
        </>
      }
    >
      {step === 'select-book' && !error && (
        <BookSelector
          selectedBook={book}
          onConfirmBook={confirmBook}
          onSelectBook={setBook}
        />
      )}
      {step === 'select-toc' && !error && (
        <TableOfContentsPicker
          entries={tableOfContents || []}
          isLoading={!tableOfContents}
          selectedEntry={tocEntry}
          onSelectEntry={entry =>
            setContentRange({ type: 'toc', start: entry })
          }
          onConfirmEntry={confirmChapter}
        />
      )}
      {error && (
        <ErrorDisplay
          description={
            step === 'select-book'
              ? 'Unable to fetch books'
              : 'Unable to fetch book contents'
          }
          error={error}
        />
      )}
    </ModalDialog>
  );
}
