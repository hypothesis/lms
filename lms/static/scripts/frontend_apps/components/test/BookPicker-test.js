import { mount } from 'enzyme';

import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitForElement } from '../../../test-util/wait';
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
      fetchChapters: sinon
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
    const chapterList = wrapper.find('ChapterList');
    const chapter = chapterList.prop('chapters')[index];
    act(() => {
      chapterList.prop('onSelectChapter')(chapter);
    });
    wrapper.update();
    return chapter;
  };

  const clickSelectButton = wrapper => {
    act(() => {
      wrapper
        .find('LabeledButton[data-testid="select-button"]')
        .prop('onClick')();
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
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    assert.isTrue(picker.find(buttonSelector).props().disabled);
    selectBook(picker);

    assert.isFalse(picker.find(buttonSelector).props().disabled);
    assert.equal(picker.find(buttonSelector).text(), 'Select book');
  });

  it('fetches chapters and renders chapter list when a book is selected', async () => {
    const picker = renderBookPicker();
    selectBook(picker);

    clickSelectButton(picker);

    let chapterList = picker.find('ChapterList');
    assert.isTrue(chapterList.exists());
    assert.equal(chapterList.prop('isLoading'), true);
    assert.calledWith(fakeVitalSourceService.fetchChapters, 'book1');

    await waitForElement(picker, 'ChapterList[isLoading=false]');

    // The list of chapters for the selected book should be presented once fetched.
    chapterList = picker.find('ChapterList');
    assert.equal(chapterList.prop('chapters'), fakeBookData.chapters.book1);
  });

  it('invokes `onSelectBook` callback after a book and chapter are chosen', async () => {
    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({ onSelectBook });

    const book = selectBook(picker);
    clickSelectButton(picker);

    await waitForElement(picker, 'ChapterList[isLoading=false]');
    const chapter = selectChapter(picker);
    clickSelectButton(picker);

    assert.calledWith(onSelectBook, book, chapter);
  });

  it('shows error that occurs while fetching chapters', async () => {
    const error = new Error('Something went wrong');
    fakeVitalSourceService.fetchChapters.rejects(error);

    const picker = renderBookPicker();
    selectBook(picker);
    clickSelectButton(picker);

    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(errorDisplay.prop('description'), 'Unable to fetch chapters');
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('ChapterList'));

    // The modal content should not have the class applied for showing the
    // list of chapters. That class makes the modal too tall for comfort when
    // displaying an error
    const modalContent = picker.find('div[role="dialog"]');
    assert.isTrue(modalContent.hasClass('LMS-Dialog--wide'));
    assert.isFalse(modalContent.hasClass('LMS-Dialog--tall'));
  });
});
