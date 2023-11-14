import {
  mockImportedComponents,
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

  const clickSelectButton = wrapper => {
    act(() => {
      wrapper.find('button[data-testid="select-button"]').prop('onClick')();
    });
    wrapper.update();
  };

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

    await waitForElement(picker, 'TableOfContentsPicker[isLoading=false]');

    // The table of contents for the selected book should be presented once fetched.
    tocPicker = picker.find('TableOfContentsPicker');
    assert.equal(tocPicker.prop('entries'), fakeBookData.chapters.book1);
  });

  it('invokes `onSelectBook` callback after a book and chapter are chosen', async () => {
    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({ onSelectBook });

    const book = selectBook(picker);
    clickSelectButton(picker);

    await waitForElement(picker, 'TableOfContentsPicker[isLoading=false]');
    const chapter = selectChapter(picker);
    clickSelectButton(picker);

    assert.calledWith(onSelectBook, book, chapter);
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
});
