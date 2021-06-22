import { mount } from 'enzyme';
import { createElement } from 'preact';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitForElement } from '../../../test-util/wait';
import { VitalSourceService, withServices } from '../../services';
import * as bookData from '../../utils/vitalsource-sample-data';
import BookPicker, { $imports } from '../BookPicker';

describe('BookPicker', () => {
  let fakeVitalSourceService;

  const BookPickerWrapper = withServices(BookPicker, () => [
    [VitalSourceService, fakeVitalSourceService],
  ]);

  const renderBookPicker = (props = {}) =>
    mount(<BookPickerWrapper {...props} />);

  beforeEach(() => {
    fakeVitalSourceService = {
      fetchBooks: sinon.stub().resolves(bookData.bookList),
      fetchChapters: sinon
        .stub()
        .callsFake(async bookID => bookData.chapterData[bookID]),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      './Dialog': true,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const selectBook = (wrapper, index = 0) => {
    const bookList = wrapper.find('BookList');
    const book = bookList.prop('books')[index];
    act(() => {
      bookList.prop('onSelectBook')(book);
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

  it('fetches and displays book list when picker is opened', async () => {
    const picker = renderBookPicker();

    // The book list should initially be empty and in a loading state.
    let bookList = picker.find('BookList');
    assert.deepEqual(bookList.prop('books'), []);
    assert.isTrue(bookList.prop('isLoading'));
    assert.calledOnce(fakeVitalSourceService.fetchBooks);

    await waitForElement(picker, 'BookList[isLoading=false]');

    // The book list should display details of books once fetched.
    bookList = picker.find('BookList');
    assert.deepEqual(bookList.prop('books'), bookData.bookList);
  });

  it('fetches and displays chapter list when a book is chosen', async () => {
    // Wait for books to load and then pick the first one.
    const picker = renderBookPicker();
    await waitForElement(picker, 'BookList[isLoading=false]');

    const book = selectBook(picker);
    clickSelectButton(picker);

    // After a book is chosen, the chapter list should appear in a loading state.
    assert.isFalse(picker.exists('BookList'));
    let chapterList = picker.find('ChapterList');
    assert.isTrue(chapterList.exists());
    assert.equal(chapterList.prop('isLoading'), true);
    assert.calledWith(
      fakeVitalSourceService.fetchChapters,
      'BOOKSHELF-TUTORIAL'
    );

    await waitForElement(picker, 'ChapterList[isLoading=false]');

    // The list of chapters for the selected book should be presented once fetched.
    chapterList = picker.find('ChapterList');
    assert.equal(chapterList.prop('chapters'), bookData.chapterData[book.id]);
  });

  it('invokes `onSelectBook` callback after a book and chapter are chosen', async () => {
    const onSelectBook = sinon.stub();
    const picker = renderBookPicker({ onSelectBook });
    await waitForElement(picker, 'BookList[isLoading=false]');

    const book = selectBook(picker);
    clickSelectButton(picker);

    await waitForElement(picker, 'ChapterList[isLoading=false]');
    const chapter = selectChapter(picker);
    clickSelectButton(picker);

    assert.calledWith(onSelectBook, book, chapter);
  });

  it('shows error that occurs while fetching books', async () => {
    const error = new Error('Something went wrong');
    fakeVitalSourceService.fetchBooks.rejects(error);

    const picker = renderBookPicker();
    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(errorDisplay.prop('message'), 'Unable to fetch books');
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('BookList'));
  });

  it('shows error that occurs while fetching chapters', async () => {
    const error = new Error('Something went wrong');
    fakeVitalSourceService.fetchChapters.rejects(error);

    const picker = renderBookPicker();
    await waitForElement(picker, 'BookList[isLoading=false]');

    selectBook(picker);
    clickSelectButton(picker);

    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(errorDisplay.prop('message'), 'Unable to fetch chapters');
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('ChapterList'));
  });
});
