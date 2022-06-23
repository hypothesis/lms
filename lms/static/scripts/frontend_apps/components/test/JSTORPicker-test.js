import { mount } from 'enzyme';
import { useState } from 'preact/hooks';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
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

  function simulateMetadataFetch(wrapper, title, otherMetadata = {}) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234', {
      title,
      is_collection: false,
      ...otherMetadata,
    });
  }

  function simulateThumbnailFetch(wrapper) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234/thumbnail', {
      image: 'data:thumbnail-image-data',
    });
  }

  function toggleCheckbox(wrapper) {
    interact(wrapper, () => {
      const checkbox = wrapper.find(
        'input[data-testid="jstor-terms-checkbox"]'
      );
      checkbox.getDOMNode().click();
      checkbox.simulate('input');
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

  const getInput = wrapper => wrapper.find('TextInput').find('input');

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
        're-validates if entered URL value changes'
      );
      assert.calledWith(fakeArticleIdFromUserInput, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeArticleIdFromUserInput.callCount,
        2,
        'Does not validate URL if it has not changed from previous value'
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
        'https://www.jstor.org/stable/1234'
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

      // Second enter press won't do anything if the terms checkbox hasn't been checked
      input.getDOMNode().dispatchEvent(keyEvent);

      toggleCheckbox(wrapper);

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

      const errorMessage = wrapper.find('[data-testid="error-message"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a JSTOR article link or ID"
      );
      assert.isTrue(errorMessage.find('Icon[name="cancel"]').exists());
    });
  });

  it('displays metadata and thumbnail of selected article', () => {
    const wrapper = renderJSTORPicker();

    updateURL(wrapper);
    simulateMetadataFetch(wrapper, 'Some interesting article');
    simulateThumbnailFetch(wrapper);

    assert.include(wrapper.text(), 'Some interesting article');
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
      new Error('No such article')
    );

    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'Unable to fetch article details: No such article'
    );
  });

  it('clears metadata/thumbnail if pending URL is changed', () => {
    const wrapper = renderJSTORPicker();

    updateURL(wrapper);
    simulateMetadataFetch(wrapper);
    simulateThumbnailFetch(wrapper);

    assert.isTrue(wrapper.exists('img'));
    assert.isTrue(wrapper.exists('[data-testid="selected-book"]'));

    const input = wrapper.find('TextInput');
    interact(wrapper, () => {
      input.prop('onInput')();
    });

    assert.isFalse(wrapper.exists('img'));
    assert.isFalse(wrapper.exists('[data-testid="selected-book"]'));
  });

  it('does not enable submit button if terms are not accepted', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    updateURL(wrapper);

    // Button remains disabled while metadata is being fetched.
    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    simulateMetadataFetch(wrapper);

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);
  });

  it('enables submit button when valid JSTOR metadata has been fetched and terms accepted', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    updateURL(wrapper);
    simulateMetadataFetch(wrapper);

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    // Checking the T&Cs checkbox should enable the submit button
    toggleCheckbox(wrapper);

    assert.isFalse(wrapper.find(buttonSelector).props().disabled);
    assert.equal(wrapper.find(buttonSelector).text(), 'Submit');

    // Since the chosen item is usable (eg. not a collection), no error should
    // be displayed.
    assert.isFalse(wrapper.exists('[data-testid="error-message"]'));

    // Un-checking the T&Cs checkbox should re-disable the submit button
    toggleCheckbox(wrapper);

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);
  });

  it('disables submit button and shows error if item is a collection', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);
    updateURL(wrapper);

    simulateMetadataFetch(wrapper, 'Some book', { is_collection: true });

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.equal(
      errorMessage.text().trim(),
      'This work is a collection. Enter the link for a specific article in the collection.'
    );
  });
});
