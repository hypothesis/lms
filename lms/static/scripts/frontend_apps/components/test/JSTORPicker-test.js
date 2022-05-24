import { mount } from 'enzyme';
import { useState } from 'preact/hooks';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import JSTORPicker, { $imports } from '../JSTORPicker';

describe('JSTORPicker', () => {
  let fakeArticleIdFromURL;

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

  function simulateMetadataFetch(wrapper, title) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234', { title });
  }

  function simulateThumbnailFetch(wrapper) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234/thumbnail', {
      image: 'data:thumbnail-image-data',
    });
  }

  const renderJSTORPicker = (props = {}) => mount(<JSTORPicker {...props} />);

  beforeEach(() => {
    fakeArticleIdFromURL = sinon.stub().returns('1234');
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
        articleIdFromURL: fakeArticleIdFromURL,
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

      assert.calledOnce(fakeArticleIdFromURL);
      assert.calledWith(fakeArticleIdFromURL, 'foo');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeArticleIdFromURL.callCount,
        2,
        're-validates if entered URL value changes'
      );
      assert.calledWith(fakeArticleIdFromURL, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeArticleIdFromURL.callCount,
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

      assert.calledOnce(fakeArticleIdFromURL);
      assert.calledWith(
        fakeArticleIdFromURL,
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
      assert.calledOnce(fakeArticleIdFromURL);

      // Second enter press, after metadata has been fetched, should "confirm"
      // the valid URL.
      simulateMetadataFetch(wrapper, 'test title');
      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(onSelectURL);
      assert.calledWith(onSelectURL, 'jstor://1234');
    });

    it('validates entered URL when `IconButton` is clicked', () => {
      const wrapper = renderJSTORPicker();
      setURL(wrapper, 'foo');

      wrapper.find('IconButton button[title="Find article"]').simulate('click');

      assert.calledOnce(fakeArticleIdFromURL);
      assert.calledWith(fakeArticleIdFromURL, 'foo');
    });

    it('does not attempt to check the URL format if the field value is empty', () => {
      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeArticleIdFromURL);

      updateURL(wrapper, '');

      assert.calledOnce(fakeArticleIdFromURL);
    });

    it('shows an error if entered URL format is invalid', () => {
      fakeArticleIdFromURL.returns(null);

      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      const errorMessage = wrapper.find('[data-testid="error-message"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a JSTOR article link"
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

  it('enables submit button when a valid JSTOR URL is entered and metadata is fetched', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    updateURL(wrapper);

    // Button remains disabled while metadata is being fetched.
    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    simulateMetadataFetch(wrapper);

    // Button is enabled once fetch is complete.
    assert.isFalse(wrapper.find(buttonSelector).props().disabled);
    assert.equal(wrapper.find(buttonSelector).text(), 'Submit');
  });
});
