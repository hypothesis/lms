import {
  mockImportedComponents,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { VitalSourceService, withServices } from '../../services';
import BookPicker, { $imports } from '../BookPicker';

const fakeBookData = {
  books: {
    book1: {
      id: 'book1',
      title: 'Book One',
      cover_image: 'https://bookstore.com/covers/book1.jpg',
    },
    book2: {
      id: 'book2',
      title: 'Book Two',
      cover_image: 'https://bookstore.com/covers/book2.jpg',
    },
  },

  chapters: {
    book1: [
      {
        title: 'Chapter One',
        cfi: '/1',
        page: '1',
      },
      {
        title: 'Chapter Two',
        cfi: '/2',
        page: '10',
      },
    ],

    book2: [
      {
        title: 'Chapter A',
        cfi: '/1',
        page: '3',
      },
      {
        title: 'Chapter B',
        cfi: '/2',
        page: '7',
      },
    ],
  },
};

describe('BookPicker', () => {
  let fakeVitalSourceService;

  const BookPickerWrapper = withServices(BookPicker, () => [
    [VitalSourceService, fakeVitalSourceService],
  ]);

  const renderBookPicker = (props = {}) =>
    mount(<BookPickerWrapper {...props} />);

  beforeEach(() => {
    fakeVitalSourceService = {
      fetchDocumentURL: sinon.stub().callsFake(async selection => {
        let content;
        if (selection.content.type === 'page') {
          content = `page/${selection.content.start}`;
        } else {
          content = `cfi/${selection.content.start.cfi}`;
        }
        return `vitalsource://books/bookID/${selection.book.id}/${content}`;
      }),
      fetchTableOfContents: sinon
        .stub()
        .callsFake(async bookID => fakeBookData.chapters[bookID]),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      './Dialog': true,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const selectBook = wrapper => {
    const bookSelector = wrapper.find('BookSelector');
    const book = fakeBookData.books.book1;

    act(() => {
      bookSelector.props().onSelectBook(book);
    });

    wrapper.update();
    return book;
  };

  const selectChapter = (wrapper, index = 0) => {
    const tocPicker = wrapper.find('TableOfContentsPicker');
    const entry = tocPicker.prop('entries')[index];
    act(() => {
      tocPicker.prop('onSelectEntry')(entry);
    });
    wrapper.update();
    return entry;
  };

  /**
   * Select the page range with a given start and end number.
   *
   * Page numbers can be specified as numbers or strings.
   */
  const selectPageRange = (wrapper, start = '', end = '') => {
    const startInput = wrapper.find('input[data-testid="start-page"]');
    const endInput = wrapper.find('input[data-testid="end-page"]');
    startInput.getDOMNode().value = start.toString();
    startInput.simulate('input');
    endInput.getDOMNode().value = end.toString();
    endInput.simulate('input');
  };

  const clickSelectButton = wrapper => {
    act(() => {
      wrapper.find('button[data-testid="select-button"]').prop('onClick')();
    });
    wrapper.update();
  };

  // Wait for the table of contents to finish loading.
  const waitForTableOfContents = wrapper =>
    waitForElement(wrapper, 'TableOfContentsPicker[isLoading=false]');

  it('renders book-selector component when picker is opened', () => {
    const picker = renderBookPicker();

    const bookSelector = picker.find('BookSelector');
    // No book has been selected yet
    assert.isNull(bookSelector.prop('selectedBook'));
  });

  it('enables submit button when a book is selected', () => {
    const picker = renderBookPicker();
    const buttonSelector = 'button[data-testid="select-button"]';

    assert.isTrue(picker.find(buttonSelector).props().disabled);
    selectBook(picker);

    assert.isFalse(picker.find(buttonSelector).props().disabled);
    assert.equal(picker.find(buttonSelector).text(), 'Select book');
  });

  it('cancels the dialog when Cancel button clicked', () => {
    const fakeCancel = sinon.stub();
    const wrapper = renderBookPicker({ onCancel: fakeCancel });

    act(() => {
      wrapper.find('button[data-testid="cancel-button"]').simulate('click');
    });
    wrapper.update();

    assert.calledOnce(fakeCancel);
  });

  it('fetches table of contents and renders picker when a book is selected', async () => {
    const picker = renderBookPicker();
    selectBook(picker);

    clickSelectButton(picker);

    let tocPicker = picker.find('TableOfContentsPicker');
    assert.isTrue(tocPicker.exists());
    assert.equal(tocPicker.prop('isLoading'), true);
    assert.calledWith(fakeVitalSourceService.fetchTableOfContents, 'book1');

    await waitForTableOfContents(picker);

    // The table of contents for the selected book should be presented once fetched.
    tocPicker = picker.find('TableOfContentsPicker');
    assert.equal(tocPicker.prop('entries'), fakeBookData.chapters.book1);
  });

  [
    // nb. We don't test all cases here. See `isPageRangeValid` tests for more.
    {
      start: '',
      end: '',
      valid: false,
    },
    {
      start: '10',
      end: '',
      valid: false,
    },
    {
      start: '10',
      end: '20',
      valid: true,
    },
    {
      start: '20',
      end: '10',
      valid: false,
    },
  ].forEach(({ start, end, valid }) => {
    it('enables final submit button when a valid page range is selected', async () => {
      const picker = renderBookPicker({ allowPageRangeSelection: true });
      const buttonSelector = 'button[data-testid="select-button"]';

      selectBook(picker);
      clickSelectButton(picker);
      await waitForTableOfContents(picker);
      selectPageRange(picker, start, end);

      assert.equal(picker.find(buttonSelector).props().disabled, !valid);
    });
  });

  [true, false].forEach(allowPageRangeSelection => {
    it('displays page range picker if feature enabled', () => {
      const picker = renderBookPicker({ allowPageRangeSelection });
      selectBook(picker);
      clickSelectButton(picker);
      assert.equal(
        picker.find('input[data-testid="start-page"]').exists(),
        allowPageRangeSelection
      );
      assert.equal(
        picker.find('input[data-testid="end-page"]').exists(),
        allowPageRangeSelection
      );
    });
  });

  it('displays page numbers corresponding to selected chapter', async () => {
    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({
      allowPageRangeSelection: true,
      onSelectBook,
    });

    selectBook(picker);
    clickSelectButton(picker);

    await waitForTableOfContents(picker);
    selectChapter(picker);

    const startInput = picker.find('input[data-testid="start-page"]');
    const endInput = picker.find('input[data-testid="end-page"]');
    assert.equal(startInput.prop('placeholder'), '1');
    assert.equal(endInput.prop('placeholder'), '10');
  });

  [
    { allowPageRangeSelection: true },
    { allowPageRangeSelection: false },
  ].forEach(({ allowPageRangeSelection }) => {
    it('invokes `onSelectBook` callback after a book and chapter are chosen', async () => {
      const onSelectBook = sinon.stub();
      const picker = renderBookPicker({
        allowPageRangeSelection,
        onSelectBook,
      });

      const book = selectBook(picker);
      clickSelectButton(picker);

      await waitForTableOfContents(picker);
      const chapter = selectChapter(picker);
      clickSelectButton(picker);

      const expectedEnd = allowPageRangeSelection
        ? fakeBookData.chapters.book1[1] // Start of chapter after selection
        : undefined;

      await waitFor(() => onSelectBook.called);
      assert.calledWith(
        onSelectBook,
        {
          book,
          content: {
            type: 'toc',
            start: chapter,
            end: expectedEnd,
          },
        },
        'vitalsource://books/bookID/book1/cfi//1'
      );
    });
  });

  it('invokes `onSelectBook` callback after a book and page range are chosen', async () => {
    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({
      allowPageRangeSelection: true,
      onSelectBook,
    });

    const book = selectBook(picker);
    clickSelectButton(picker);

    await waitForTableOfContents(picker);
    selectPageRange(picker, 10, 20);
    clickSelectButton(picker);

    await waitFor(() => onSelectBook.called);
    assert.calledWith(
      onSelectBook,
      {
        book,
        content: {
          type: 'page',
          start: '10',
          end: '20',
        },
      },
      'vitalsource://books/bookID/book1/page/10'
    );
  });

  it('shows error that occurs while fetching table of contents', async () => {
    const error = new Error('Something went wrong');
    fakeVitalSourceService.fetchTableOfContents.rejects(error);

    const picker = renderBookPicker();
    selectBook(picker);
    clickSelectButton(picker);

    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(
      errorDisplay.prop('description'),
      'Unable to fetch book contents'
    );
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('TableOfContentsPicker'));
  });

  it('shows error that occurs while fetching document URL', async () => {
    const error = new Error('Something went wrong');
    fakeVitalSourceService.fetchDocumentURL.rejects(error);

    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({ onSelectBook });

    selectBook(picker);
    clickSelectButton(picker);

    await waitForTableOfContents(picker);
    selectChapter(picker);
    clickSelectButton(picker);

    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(
      errorDisplay.prop('description'),
      'Unable to fetch book contents'
    );
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('TableOfContentsPicker'));
  });
});
