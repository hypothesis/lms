import { mount } from 'enzyme';
import { createElement } from 'preact';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitForElement } from '../../../test-util/wait';
import * as bookData from '../../utils/vitalsource-sample-data';
import BookPicker, { $imports } from '../BookPicker';

describe('BookPicker', () => {
  let fakeAPI;

  const renderBookPicker = (props = {}) =>
    mount(<BookPicker authToken="dummy-auth-token" {...props} />);

  beforeEach(() => {
    fakeAPI = {
      fetchBooks: sinon.stub().resolves(bookData.bookList),
      fetchChapters: sinon
        .stub()
        .callsFake(async (authToken, bookID) => bookData.chapterData[bookID]),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      './Dialog': true,
    });
    $imports.$mock({
      '../utils/api': fakeAPI,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const selectBook = wrapper => {
    const bookList = wrapper.find('BookList');
    const book = bookList.prop('books')[0];
    act(() => {
      bookList.prop('onSelectBook')(book);
    });
    wrapper.update();
    return book;
  };

  const selectChapter = wrapper => {
    const chapterList = wrapper.find('ChapterList');
    const chapter = chapterList.prop('chapters')[0];
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

    let bookList = picker.find('BookList');
    assert.deepEqual(bookList.prop('books'), []);
    assert.isTrue(bookList.prop('isLoading'));
    assert.calledWith(fakeAPI.fetchBooks, 'dummy-auth-token');

    await waitForElement(picker, 'BookList[isLoading=false]');

    bookList = picker.find('BookList');
    assert.deepEqual(bookList.prop('books'), bookData.bookList);
  });

  it('fetches and displays chapter list when a book is chosen', async () => {
    const picker = renderBookPicker();
    await waitForElement(picker, 'BookList[isLoading=false]');

    const book = selectBook(picker);
    clickSelectButton(picker);

    assert.isFalse(picker.exists('BookList'));
    let chapterList = picker.find('ChapterList');
    assert.isTrue(chapterList.exists());
    assert.equal(chapterList.prop('isLoading'), true);
    assert.calledWith(fakeAPI.fetchChapters, 'dummy-auth-token');

    await waitForElement(picker, 'ChapterList[isLoading=false]');

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
    fakeAPI.fetchBooks.rejects(error);

    const picker = renderBookPicker();
    const errorDisplay = await waitForElement(picker, 'ErrorDisplay');

    assert.equal(errorDisplay.prop('message'), 'Unable to fetch books');
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(picker.exists('BookList'));
  });

  it('shows error that occurs while fetching chapters', async () => {
    const error = new Error('Something went wrong');
    fakeAPI.fetchChapters.rejects(error);

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
