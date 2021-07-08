import { mount } from 'enzyme';
import { createElement } from 'preact';

import { waitFor, waitForElement } from '../../../test-util/wait';
import { VitalSourceService, withServices } from '../../services';
import * as bookData from '../../utils/vitalsource-sample-data';
import BookSelector, { $imports } from '../BookSelector';

describe('BookSelector', () => {
  let fakeVitalSourceService;
  let fakeBookIDFromURL;

  const BookSelectorWrapper = withServices(BookSelector, () => [
    [VitalSourceService, fakeVitalSourceService],
  ]);

  const renderBookSelector = (props = {}) =>
    mount(<BookSelectorWrapper onSelectBook={sinon.stub()} {...props} />);

  beforeEach(() => {
    fakeBookIDFromURL = sinon.stub().returns('BOOKSHELF_TUTORIAL');
    fakeVitalSourceService = {
      fetchBook: sinon.stub().callsFake(async () => bookData.bookList[0]),
    };

    $imports.$mock({
      '../utils/vitalsource': {
        bookIDFromURL: fakeBookIDFromURL,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getInput = wrapper => wrapper.find('TextInput').find('input');

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

  context('entering, changing and submitting book URL', () => {
    it('validates entered URL when the value of the text input changes', () => {
      const wrapper = renderBookSelector();

      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeBookIDFromURL);
      assert.calledWith(fakeBookIDFromURL, 'foo');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeBookIDFromURL.callCount,
        2,
        're-validates if entered URL value changes'
      );
      assert.calledWith(fakeBookIDFromURL, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeBookIDFromURL.callCount,
        2,
        'Does not validate URL if it has not changed from previous value'
      );
    });

    it('validates entered URL when input is focused and "Enter" is pressed', () => {
      const wrapper = renderBookSelector();
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'http://www.example.com');

      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(fakeBookIDFromURL);
      assert.calledWith(fakeBookIDFromURL, 'http://www.example.com');
    });

    it('validates entered URL when `IconButton` is clicked', () => {
      const wrapper = renderBookSelector();
      setURL(wrapper, 'foo');

      wrapper.find('IconButton button[title="Find book"]').simulate('click');

      assert.calledOnce(fakeBookIDFromURL);
      assert.calledWith(fakeBookIDFromURL, 'foo');
    });

    it('does not attempt to check the URL format if the field value is empty', () => {
      const wrapper = renderBookSelector();
      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeBookIDFromURL);

      updateURL(wrapper, '');

      assert.calledOnce(fakeBookIDFromURL);
    });

    it('shows an error if entered URL format is invalid', () => {
      fakeBookIDFromURL.returns(null);

      const wrapper = renderBookSelector();
      updateURL(wrapper, 'foo');

      const errorMessage = wrapper.find('[data-testid="error-message"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a VitalSource book link"
      );
      assert.isTrue(errorMessage.find('SvgIcon[name="cancel"]').exists());
    });
  });

  context('correctly-formatted URL entered', () => {
    it('fetches book metadata associated with the entered URL', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });
      updateURL(wrapper, 'a valid URL');

      await waitFor(() => onSelectBook.called);

      assert.calledWith(fakeVitalSourceService.fetchBook, 'BOOKSHELF_TUTORIAL');
      assert.calledOnce(onSelectBook);
      assert.calledWith(onSelectBook, bookData.bookList[0]);
    });

    it('clears any existing book metadata before loading and selecting new book', async () => {
      const onSelectBook = sinon.stub();
      const selectedBook = bookData.bookList[0];
      const wrapper = renderBookSelector({ onSelectBook, selectedBook });

      updateURL(wrapper, 'a valid URL');

      await waitFor(() => onSelectBook.called);

      assert.equal(onSelectBook.callCount, 2);
      assert.equal(
        onSelectBook.getCall(0).args[0],
        null,
        'clears the pre-existing selected book'
      );
      assert.equal(
        onSelectBook.getCall(1).args[0],
        bookData.bookList[0],
        'selects the newly-fetched book'
      );
    });

    it('disables input and associated button while fetching', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });
      updateURL(wrapper, 'a valid URL');

      const input = getInput(wrapper);
      const iconButton = wrapper.find('IconButton button[title="Find book"]');

      assert.isTrue(input.props().disabled);
      assert.isTrue(iconButton.props().disabled);

      await waitForElement(wrapper, 'IconButton[disabled=false]');

      assert.isFalse(getInput(wrapper).props().disabled);
    });

    it('shows cover thumbnail in loading state while fetching', async () => {
      const onSelectBook = sinon.stub();
      const wrapper = renderBookSelector({ onSelectBook });

      assert.isFalse(wrapper.find('Thumbnail img').exists());

      updateURL(wrapper, 'a valid URL');

      assert.isTrue(wrapper.find('Thumbnail').props().isLoading);

      await waitForElement(wrapper, 'Thumbnail[isLoading=false]');
    });

    context('a book has been loaded and selected', () => {
      it('sets the cover image and title when book is provided', async () => {
        const wrapper = renderBookSelector({
          selectedBook: bookData.bookList[0],
        });

        const selectedBook = wrapper.find('[data-testid="selected-book"]');

        assert.isTrue(wrapper.find('Thumbnail img').exists());
        assert.include(selectedBook.text(), 'Bookshelf Tutorial');
        assert.isTrue(selectedBook.find('SvgIcon[name="check"]').exists());
      });
    });

    context('book metadata fetch failed', () => {
      it('shows error from service exception', async () => {
        const error = new Error('Something went wrong');
        fakeVitalSourceService.fetchBook.rejects(error);

        const wrapper = renderBookSelector();
        updateURL(wrapper, 'foo');

        await waitForElement(wrapper, '[data-testid="error-message"]');

        const errorMessage = wrapper.find('[data-testid="error-message"]');
        assert.include(errorMessage.text(), 'Something went wrong');
      });
    });
  });
});
