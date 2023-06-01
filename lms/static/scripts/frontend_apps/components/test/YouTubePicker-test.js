import { mount } from 'enzyme';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { APIError } from '../../errors';
import YouTubePicker, { $imports } from '../YouTubePicker';

describe('YouTubePicker', () => {
  let fakeUseAPIFetch;
  let fakeOnCancel;
  let fakeOnSelectURL;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().returns({});
    fakeOnCancel = sinon.stub();
    fakeOnSelectURL = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/api': { useAPIFetch: fakeUseAPIFetch },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderComponent = (props = {}) =>
    mount(
      <YouTubePicker
        onCancel={fakeOnCancel}
        onSelectURL={fakeOnSelectURL}
        defaultURL="https://youtu.be/videoId"
        {...props}
      />
    );

  it('invokes `onCancel` when dialog is closed', () => {
    const wrapper = renderComponent();

    wrapper.find('ModalDialog').props().onClose();
    assert.called(fakeOnCancel);
  });

  it('invokes `onCancel` when Cancel button is clicked', () => {
    const wrapper = renderComponent();

    wrapper.find('button[data-testid="cancel-button"]').props().onClick();
    assert.called(fakeOnCancel);
  });

  it('invokes `onSelectURL` when Continue button is clicked', () => {
    const wrapper = renderComponent();

    wrapper.find('button[data-testid="select-button"]').props().onClick();
    assert.calledWith(fakeOnSelectURL, 'youtube://videoId');
  });

  [undefined, 'not-a-youtube-url'].forEach(defaultURL => {
    it('disables Continue button as long as a valid URL has not been set', () => {
      const wrapper = renderComponent({ defaultURL });
      assert.isTrue(
        wrapper.find('button[data-testid="select-button"]').prop('disabled')
      );
    });
  });

  [
    { data: undefined, isDisabled: true },
    { data: {}, isDisabled: false },
  ].forEach(({ data, isDisabled }) => {
    it('disables Continue button as long as no data is loaded from API', () => {
      fakeUseAPIFetch.returns({ data });

      const wrapper = renderComponent({ defaultURL: 'https://youtu.be/123' });
      assert.equal(
        wrapper.find('button[data-testid="select-button"]').prop('disabled'),
        isDisabled
      );
    });
  });

  it('sets validation error when trying to set an invalid URL', () => {
    const wrapper = renderComponent();

    // Invoking onURLChange with an invalid URL will set the error
    wrapper.find('URLFormWithPreview').props().onURLChange('not-a-youtube-url');
    wrapper.update();

    assert.isDefined(wrapper.find('URLFormWithPreview').prop('error'));

    // Invoking onURLChange with a valid URL will remove the error above
    wrapper
      .find('URLFormWithPreview')
      .props()
      .onURLChange('https://youtube.com/watch?v=videoId');
    wrapper.update();

    assert.isUndefined(wrapper.find('URLFormWithPreview').prop('error'));
  });

  it('displays video info when available', () => {
    fakeUseAPIFetch.returns({
      data: {
        title: 'The video title',
        channel: 'Hypothesis',
      },
    });

    const wrapper = renderComponent();
    const metadata = wrapper.find('[data-testid="selected-video"]');

    assert.isTrue(metadata.exists());
    assert.equal(metadata.text(), 'The video title (Hypothesis)');
  });

  it('displays expected thumbnail based on API request', () => {
    fakeUseAPIFetch.returns({
      isLoading: false,
      data: {
        title: 'The video title',
        image: 'https://i.ytimg.com/vi/9l55oKI_Ch8/mqdefault.jpg',
      },
    });

    const wrapper = renderComponent();
    const thumbnail = wrapper.find('URLFormWithPreview').prop('thumbnail');

    assert.isFalse(thumbnail.isLoading);
    assert.equal(
      thumbnail.image,
      'https://i.ytimg.com/vi/9l55oKI_Ch8/mqdefault.jpg'
    );
    assert.equal(thumbnail.alt, 'The video title');
    assert.equal(thumbnail.orientation, 'landscape');
  });

  [
    { errorCode: 'youtube_video_not_found', expectedError: 'Video not found' },
    {
      errorCode: 'unknown_error',
      expectedError:
        'URL must be a YouTube video, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"',
    },
  ].forEach(({ errorCode, expectedError }) => {
    it('displays error when API request fails', () => {
      fakeUseAPIFetch.returns({
        error: new APIError(400, { error_code: errorCode }),
      });

      const wrapper = renderComponent();

      assert.equal(
        wrapper.find('URLFormWithPreview').prop('error'),
        expectedError
      );
    });
  });

  it('resets visible errors on URL input', () => {
    const wrapper = renderComponent();

    // Invoking onURLChange with an invalid URL will set the error
    wrapper.find('URLFormWithPreview').props().onURLChange('not-a-youtube-url');
    wrapper.update();
    assert.isDefined(wrapper.find('URLFormWithPreview').prop('error'));

    wrapper.find('URLFormWithPreview').props().onInput();
    wrapper.update();

    // As soon as input changes, the error is unset
    assert.isUndefined(wrapper.find('URLFormWithPreview').prop('error'));
  });
});
