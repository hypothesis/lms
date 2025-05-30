import { mount, waitFor, waitForElement } from '@hypothesis/frontend-testing';

import { VitalSourceService, withServices } from '../../services';
import BookSelector, { $imports } from '../BookSelector';

const fakeBookData = {
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
};

describe('BookSelector', () => {
  let fakeFormatErrorMessage;
  let fakeVitalSourceService;
  let fakeExtractBookID;

  const BookSelectorWrapper = withServices(BookSelector, () => [
    [VitalSourceService, fakeVitalSourceService],
  ]);

  const renderBookSelector = (props = {}) =>
    mount(
      <BookSelectorWrapper
        onConfirmBook={sinon.stub()}
        onSelectBook={sinon.stub()}
        {...props}
      />,
    );

  beforeEach(() => {
    fakeExtractBookID = sinon.stub().returns('book1');
    fakeFormatErrorMessage = sinon.stub();
    fakeVitalSourceService = {
      fetchBook: sinon.stub().callsFake(async bookID => fakeBookData[bookID]),
    };

    $imports.$mock({
      '../errors': {
        formatErrorMessage: fakeFormatErrorMessage,
      },
      '../utils/vitalsource': {
        extractBookID: fakeExtractBookID,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getInput = wrapper =>
    wrapper.find('input[data-testid="vitalsource-input"]');

  // Set the value of the input field but do not fire any events
  const setURL = (wrapper, url) => {
    const input = getInput(wrapper);
    input.getDOMNode().value = url;
  };

  // Set the value of the input field AND fire `change` event
  const updateURL = (wrapper, url) => {
    setURL(wrapper, url);
    const input = getInput(wrapper);
    input.simulate('change');
  };

  describe('initial focus', () => {
    it('focuses the URL text input element', () => {
      const beforeFocused = document.activeElement;

      const wrapper = mount(
        <BookSelectorWrapper onSelectBook={sinon.stub()} />,
        {
          connected: true,
        },
      );

      const focused = document.activeElement;
      const input = wrapper.find('input[name="vitalSourceURL"]').getDOMNode();

      assert.notEqual(beforeFocused, focused);
      assert.equal(focused, input);
    });
  });

  context('entering, changing and submitting book URL', () => {
    it('validates entered URL when the value of the text input changes', () => {
      const wrapper = renderBookSelector();

      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeExtractBookID);
      assert.calledWith(fakeExtractBookID, 'foo');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeExtractBookID.callCount,
        2,
        're-validates if entered URL value changes',
      );
      assert.calledWith(fakeExtractBookID, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeExtractBookID.callCount,
        2,
        'Does not validate URL if it has not changed from previous value',
      );
    });

    it('validates entered URL when input is focused and "Enter" is pressed', () => {
      const wrapper = renderBookSelector();
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'http://www.example.com');

      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(fakeExtractBookID);
      assert.calledWith(fakeExtractBookID, 'http://www.example.com');
    });

    it('confirms the selected book if "Enter" is pressed subsequently', () => {
      const onConfirmBook = sinon.stub();
      const selectedBook = fakeBookData.book1;
      const wrapper = renderBookSelector({ onConfirmBook, selectedBook });
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'http://www.example.com');

      // First enter press will "look up" book from entered URL
      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(fakeExtractBookID);

      // Second enter press should "confirm" the book looked up after the
      // first press
      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(onConfirmBook);
      assert.calledWith(onConfirmBook, selectedBook);
    });

    it('validates entered URL when `IconButton` is clicked', () => {
      const wrapper = renderBookSelector();
      setURL(wrapper, 'foo');

      wrapper.find('IconButton button[title="Find book"]').simulate('click');

      assert.calledOnce(fakeExtractBookID);
      assert.calledWith(fakeExtractBookID, 'foo');
    });

    it('does not attempt to check the URL format if the field value is empty', () => {
      const wrapper = renderBookSelector();
      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeExtractBookID);

      updateURL(wrapper, '');

      assert.calledOnce(fakeExtractBookID);
    });

    it('shows an error if entered URL format is invalid', () => {
      fakeExtractBookID.returns(null);

      const wrapper = renderBookSelector();
      updateURL(wrapper, 'foo');

      const errorMessage = wrapper.find('UIMessage[status="error"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a VitalSource book link",
      );
      assert.isTrue(errorMessage.find('CancelIcon').exists());
    });
  });

  context('correctly-formatted URL entered', () => {
    it('fetches book metadata associated with the entered URL', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });
      updateURL(wrapper, 'a valid URL');

      await waitFor(() => onSelectBook.called);

      assert.calledWith(fakeVitalSourceService.fetchBook, 'book1');
      assert.calledOnce(onSelectBook);
      assert.calledWith(onSelectBook, fakeBookData.book1);
    });

    it('clears any existing book metadata before loading and selecting new book', async () => {
      const onSelectBook = sinon.stub();
      const selectedBook = fakeBookData.book1;
      const wrapper = renderBookSelector({ onSelectBook, selectedBook });

      updateURL(wrapper, 'a valid URL');

      await waitFor(() => onSelectBook.called);

      assert.equal(onSelectBook.callCount, 2);
      assert.equal(
        onSelectBook.getCall(0).args[0],
        null,
        'clears the pre-existing selected book',
      );
      assert.equal(
        onSelectBook.getCall(1).args[0],
        fakeBookData.book1,
        'selects the newly-fetched book',
      );
    });

    it('makes input read-only while fetching', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });
      assert.isFalse(getInput(wrapper).props().readOnly);

      updateURL(wrapper, 'a valid URL');

      const input = getInput(wrapper);
      assert.isTrue(input.props().readOnly);
      await waitForElement(wrapper, 'input[readOnly=false]');
    });

    it('shows cover thumbnail in loading state while fetching', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });

      assert.isFalse(wrapper.find('Thumbnail img').exists());

      updateURL(wrapper, 'a valid URL');

      assert.isTrue(wrapper.find('Thumbnail').props().loading);

      await waitForElement(wrapper, 'Thumbnail[loading=false]');
    });

    context('a book has been loaded and selected', () => {
      it('sets the cover image and title when book is provided', async () => {
        const wrapper = renderBookSelector({
          selectedBook: fakeBookData.book1,
        });

        const selectedBook = wrapper.find('UIMessage[status="success"]');

        assert.isTrue(wrapper.find('Thumbnail img').exists());
        assert.include(selectedBook.text(), 'Book One');
      });
    });

    context('book metadata fetch failed', () => {
      it('shows error from service exception', async () => {
        fakeFormatErrorMessage.returns('Something went wrong');
        const error = new Error('Any old error');
        fakeVitalSourceService.fetchBook.rejects(error);

        const wrapper = renderBookSelector();
        updateURL(wrapper, 'foo');

        await waitForElement(wrapper, 'UIMessage[status="error"]');

        assert.calledWith(fakeFormatErrorMessage, error);
        const errorMessage = wrapper.find('UIMessage[status="error"]');
        assert.include(errorMessage.text(), 'Something went wrong');
      });
    });
  });
});
