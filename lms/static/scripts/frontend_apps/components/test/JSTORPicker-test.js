import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { useState } from 'preact/hooks';
import { act } from 'preact/test-utils';

import JSTORPicker, { $imports } from '../JSTORPicker';

describe('JSTORPicker', () => {
  let fakeArticleIdFromUserInput;

  // Map of API path => fetch result state setter.
  let setAPIFetchResult;

  function interact(wrapper, callback) {
    act(callback);
    wrapper.update();
  }

  function simulateAPIFetch(wrapper, path, data, error = null) {
    act(() => {
      setAPIFetchResult[path]({
        data,
        error,
        isLoading: false,
      });
    });
    wrapper.update();
  }

  function simulateMetadataFetch(
    wrapper,
    title = undefined,
    otherMetadata = {},
  ) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234', {
      item: {
        title: title,
        subtitle: 'The sequel',
      },
      content_status: 'available',
      ...otherMetadata,
    });
  }

  function simulateThumbnailFetch(wrapper) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234/thumbnail', {
      image: 'data:thumbnail-image-data',
    });
  }

  const renderJSTORPicker = (props = {}) => mount(<JSTORPicker {...props} />);

  beforeEach(() => {
    fakeArticleIdFromUserInput = sinon.stub().returns('1234');
    setAPIFetchResult = {};

    function useAPIFetchFake(path) {
      const [result, setResult] = useState({
        data: null,
        error: null,
        isLoading: false,
      });
      setAPIFetchResult[path] = setResult;

      if (!path) {
        return { data: null, error: null, isLoading: false };
      }

      return result;
    }

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/api': {
        useAPIFetch: useAPIFetchFake,
      },
      '../utils/jstor': {
        articleIdFromUserInput: fakeArticleIdFromUserInput,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getInput = wrapper => wrapper.find('Input').find('input');

  // Set the value of the input field but do not fire any events
  const setURL = (wrapper, url) => {
    const input = getInput(wrapper);
    input.getDOMNode().value = url;
  };

  // Set the value of the input field AND fire `change` event
  const updateURL = (wrapper, url = 'foo') => {
    setURL(wrapper, url);
    const input = getInput(wrapper);
    input.simulate('change');
  };

  describe('initial focus', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      document.body.appendChild(container);
    });

    afterEach(() => {
      container.remove();
    });

    it('focuses the URL text input element', () => {
      const beforeFocused = document.activeElement;

      const wrapper = mount(<JSTORPicker onSelectURL={sinon.stub()} />, {
        attachTo: container,
      });

      const focused = document.activeElement;
      const input = wrapper.find('input[name="jstorURL"]').getDOMNode();

      assert.notEqual(beforeFocused, focused);
      assert.equal(focused, input);
    });
  });

  it('pre-fills input field with `defaultArticle` value and fetches article metadata/thumbnail', () => {
    const wrapper = mount(<JSTORPicker defaultArticle="1234" />);

    // Input field should use existing article ID.
    const input = wrapper.find('input[name="jstorURL"]').getDOMNode();
    assert.equal(input.value, '1234');

    // The metadata and thumbnail for the existing article should be fetched.
    assert.calledWith(fakeArticleIdFromUserInput, '1234');
    simulateMetadataFetch(wrapper, 'Test article');
    simulateThumbnailFetch(wrapper);
    assert.include(wrapper.text(), 'Test article');
    assert.equal(wrapper.find('img').prop('src'), 'data:thumbnail-image-data');
  });

  context('entering, changing and submitting article URL', () => {
    it('validates entered URL when the value of the text input changes', () => {
      const wrapper = renderJSTORPicker();

      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeArticleIdFromUserInput);
      assert.calledWith(fakeArticleIdFromUserInput, 'foo');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeArticleIdFromUserInput.callCount,
        2,
        're-validates if entered URL value changes',
      );
      assert.calledWith(fakeArticleIdFromUserInput, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeArticleIdFromUserInput.callCount,
        2,
        'Does not validate URL if it has not changed from previous value',
      );
    });

    it('validates entered URL when input is focused and "Enter" is pressed', () => {
      const wrapper = renderJSTORPicker();
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'https://www.jstor.org/stable/1234');

      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(fakeArticleIdFromUserInput);
      assert.calledWith(
        fakeArticleIdFromUserInput,
        'https://www.jstor.org/stable/1234',
      );
    });

    it('confirms the validated URL if "Enter" is pressed subsequently', () => {
      const onSelectURL = sinon.stub();
      const wrapper = renderJSTORPicker({ onSelectURL });
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'https://www.jstor.org/stable/1234');

      // First enter press will validate URL
      interact(wrapper, () => {
        input.getDOMNode().dispatchEvent(keyEvent);
      });
      assert.calledOnce(fakeArticleIdFromUserInput);

      simulateMetadataFetch(wrapper, 'test title');

      // Enter will submit if terms are checked and there is valid metadata fetched
      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(onSelectURL);
      assert.calledWith(onSelectURL, 'jstor://1234');
    });

    it('validates entered URL when `IconButton` is clicked', () => {
      const wrapper = renderJSTORPicker();
      setURL(wrapper, 'foo');

      wrapper.find('IconButton button[title="Find article"]').simulate('click');

      assert.calledOnce(fakeArticleIdFromUserInput);
      assert.calledWith(fakeArticleIdFromUserInput, 'foo');
    });

    it('does not attempt to check the URL format if the field value is empty', () => {
      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeArticleIdFromUserInput);

      updateURL(wrapper, '');

      assert.calledOnce(fakeArticleIdFromUserInput);
    });

    it('shows an error if entered URL format is invalid', () => {
      fakeArticleIdFromUserInput.returns(null);

      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      const errorMessage = wrapper.find('UIMessage[status="error"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a JSTOR article link or ID",
      );
    });
  });

  it('displays metadata and thumbnail of selected article', () => {
    const wrapper = renderJSTORPicker();

    updateURL(wrapper);
    simulateMetadataFetch(wrapper, 'Some interesting article');
    simulateThumbnailFetch(wrapper);

    assert.include(wrapper.text(), 'Some interesting article: The sequel');
    const thumbnail = wrapper.find('img');
    assert.equal(thumbnail.prop('src'), 'data:thumbnail-image-data');
  });

  it('displays error if metadata cannot be fetched', () => {
    const wrapper = renderJSTORPicker();

    updateURL(wrapper);
    simulateAPIFetch(
      wrapper,
      '/api/jstor/articles/1234',
      null,
      new Error('No such article'),
    );

    const errorMessage = wrapper.find('UIMessage[status="error"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'Unable to fetch article details: No such article',
    );
  });

  it('clears metadata/thumbnail if pending URL is changed', () => {
    const wrapper = renderJSTORPicker();

    updateURL(wrapper);
    simulateMetadataFetch(wrapper);
    simulateThumbnailFetch(wrapper);

    assert.isTrue(wrapper.exists('img'));
    assert.isTrue(wrapper.exists('[data-testid="selected-book"]'));

    const input = wrapper.find('Input');
    interact(wrapper, () => {
      input.prop('onInput')();
    });

    assert.isFalse(wrapper.exists('img'));
    assert.isFalse(wrapper.exists('[data-testid="selected-book"]'));
  });

  it('enables submit button when valid JSTOR metadata has been fetched', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'Button[data-testid="select-button"]';

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    updateURL(wrapper);
    simulateMetadataFetch(wrapper);

    assert.isFalse(wrapper.find(buttonSelector).props().disabled);
    assert.equal(wrapper.find(buttonSelector).text(), 'Accept and continue');

    // Since the chosen item is usable (eg. not a collection), no error should
    // be displayed.
    assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
  });

  it('enables submit button when valid same JSTOR article is input more than once', () => {
    const onSelectURL = sinon.stub();
    const wrapper = renderJSTORPicker({ onSelectURL });
    const buttonSelector = 'Button[data-testid="select-button"]';

    // We update the article once, which will enable the select button
    assert.isTrue(wrapper.find(buttonSelector).props().disabled);
    updateURL(wrapper, '123456');
    simulateMetadataFetch(wrapper);
    assert.isFalse(wrapper.find(buttonSelector).props().disabled);

    // Then we simulate input on the URL field. This will disable the button
    getInput(wrapper).props().onInput();
    wrapper.update();
    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    // Then we update to the same article again, which should re-enable the button
    updateURL(wrapper, '123456');
    assert.isFalse(wrapper.find(buttonSelector).props().disabled);
  });

  [
    {
      contentStatus: 'no_access',
      expectedError: 'Your institution does not have access to this item.',
    },
    {
      contentStatus: 'no_content',
      expectedError:
        'There is no content available for this item. To select an item within a journal or book, enter a link to a specific article or chapter.',
    },
  ].forEach(({ contentStatus, expectedError }) => {
    it('disables submit button and shows error if content is not available', () => {
      const wrapper = renderJSTORPicker();
      const buttonSelector = 'Button[data-testid="select-button"]';

      assert.isTrue(wrapper.find(buttonSelector).props().disabled);
      updateURL(wrapper);

      simulateMetadataFetch(wrapper, 'Some book', {
        content_status: contentStatus,
      });

      assert.isTrue(wrapper.find(buttonSelector).props().disabled);

      const errorMessage = wrapper.find('UIMessage[status="error"]');
      assert.isTrue(errorMessage.exists());
      assert.equal(errorMessage.text().trim(), expectedError);
    });
  });
});
