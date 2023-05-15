import { mount } from 'enzyme';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import YouTubePicker, { $imports } from '../YouTubePicker';

describe('YouTubePicker', () => {
  let fakeUseYouTubeVideoInfo;
  let fakeOnCancel;
  let fakeOnSelectURL;

  beforeEach(() => {
    fakeUseYouTubeVideoInfo = sinon.stub().returns({});
    fakeOnCancel = sinon.stub();
    fakeOnSelectURL = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/youtube': { useYouTubeVideoInfo: fakeUseYouTubeVideoInfo },
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

  it('displays video metadata when available', () => {
    fakeUseYouTubeVideoInfo.returns({
      metadata: {
        title: 'The video title',
        channel: 'Hypothesis',
      },
    });

    const wrapper = renderComponent();
    const metadata = wrapper.find('[data-testid="selected-video"]');

    assert.isTrue(metadata.exists());
    assert.equal(metadata.text(), 'The video title (Hypothesis)');
  });

  it('resets error when the URL is empty', () => {
    const wrapper = renderComponent();

    wrapper.find('URLFormWithPreview').props().onURLChange('not-a-youtube-url');
    wrapper.update();
    assert.isDefined(wrapper.find('URLFormWithPreview').prop('error'));

    wrapper.find('URLFormWithPreview').props().onURLChange('');
    wrapper.update();
    assert.isUndefined(wrapper.find('URLFormWithPreview').prop('error'));
  });

  it('resets select button when the URL is empty', () => {
    const wrapper = renderComponent();

    assert.isFalse(
      wrapper.find('button[data-testid="select-button"]').prop('disabled')
    );

    wrapper.find('URLFormWithPreview').props().onURLChange('');
    wrapper.update();
    assert.isTrue(
      wrapper.find('button[data-testid="select-button"]').prop('disabled')
    );
  });
});
