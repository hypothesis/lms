import { mount } from 'enzyme';
import { useState } from 'preact/hooks';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import JSTORPicker, { $imports } from '../JSTORPicker';

describe('JSTORPicker', () => {
  let fakeArticleIdFromUserInput;

  // Map of API path => fetch result state setter.
  let setAPIFetchResult;

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
    otherMetadata = {}
  ) {
    simulateAPIFetch(wrapper, '/api/jstor/articles/1234', {
      item: {
        title,
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

  const getForm = wrapper => wrapper.find('URLFormWithPreview');

  // Set the value of the input field AND fire `change` event
  const updateURL = (wrapper, url = 'foo') => {
    const form = getForm(wrapper);
    form.props().onURLChange(url);
    wrapper.update();
  };

  it('pre-fills input field with `defaultArticle` value and fetches article metadata/thumbnail', () => {
    const wrapper = mount(<JSTORPicker defaultArticle="1234" />);

    // Form should use existing article ID.
    assert.equal(getForm(wrapper).prop('defaultURL'), '1234');

    // The metadata and thumbnail for the existing article should be fetched.
    assert.calledWith(fakeArticleIdFromUserInput, '1234');
    simulateMetadataFetch(wrapper, 'Test article');
    simulateThumbnailFetch(wrapper);
    assert.include(wrapper.text(), 'Test article');
    assert.equal(
      getForm(wrapper).prop('thumbnail').image,
      'data:thumbnail-image-data'
    );
  });

  context('submitting article URL', () => {
    it('validates entered URL when changed', () => {
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

    it('confirms the validated URL if select button is clicked', () => {
      const onSelectURL = sinon.stub();
      const wrapper = renderJSTORPicker({
        onSelectURL,
        defaultArticle: '1234',
      });

      simulateMetadataFetch(wrapper, 'test title');

      wrapper
        .find('Button[data-testid="select-button"]')
        .find('button')
        .simulate('click');

      assert.calledOnce(onSelectURL);
      assert.calledWith(onSelectURL, 'jstor://1234');
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

      const errorMessage = getForm(wrapper).prop('error');

      assert.include(
        errorMessage,
        "That doesn't look like a JSTOR article link or ID"
      );
    });
  });

  it('displays metadata and thumbnail of selected article', () => {
    const wrapper = renderJSTORPicker({ defaultArticle: '1234' });

    simulateMetadataFetch(wrapper, 'Some interesting article');
    simulateThumbnailFetch(wrapper);

    assert.include(wrapper.text(), 'Some interesting article: The sequel');
    assert.equal(
      getForm(wrapper).prop('thumbnail').image,
      'data:thumbnail-image-data'
    );
  });

  it('displays error if metadata cannot be fetched', () => {
    const wrapper = renderJSTORPicker({ defaultArticle: '1234' });

    simulateAPIFetch(
      wrapper,
      '/api/jstor/articles/1234',
      null,
      new Error('No such article')
    );

    const errorMessage = getForm(wrapper).prop('error');
    assert.include(
      errorMessage,
      'Unable to fetch article details: No such article'
    );
  });

  it('clears metadata/thumbnail if pending URL is changed', () => {
    const wrapper = renderJSTORPicker({ defaultArticle: '1234' });

    simulateMetadataFetch(wrapper);
    simulateThumbnailFetch(wrapper);

    assert.isDefined(getForm(wrapper).prop('thumbnail').image);
    assert.isTrue(wrapper.exists('[data-testid="selected-book"]'));

    updateURL(wrapper, '');

    assert.isUndefined(getForm(wrapper).prop('thumbnail').image);
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
    assert.isUndefined(getForm(wrapper).prop('error'));
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

      const errorMessage = getForm(wrapper).prop('error');
      assert.equal(errorMessage.trim(), expectedError);
    });
  });

  it("disables submit button when the input's state becomes dirty", () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'Button[data-testid="select-button"]';

    updateURL(wrapper);
    simulateMetadataFetch(wrapper);
    assert.isFalse(wrapper.find(buttonSelector).props().disabled);

    getForm(wrapper).props().onInput();
    wrapper.update();

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);
  });
});
