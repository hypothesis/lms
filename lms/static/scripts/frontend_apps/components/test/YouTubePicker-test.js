import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import YouTubePicker from '../YouTubePicker';

const validYouTubeUrl = 'https://youtu.be/cKxqzvzlnKU';

describe('YouTubePicker', () => {
  const renderPicker = (props = {}) => mount(<YouTubePicker {...props} />);

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderPicker({
      defaultURL: validYouTubeUrl,
    });
    assert.equal(
      wrapper.find('URLPickerForm').prop('defaultURL'),
      validYouTubeUrl
    );
  });

  it('invokes `onSelectURL` when user submits a valid YouTube video', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit(validYouTubeUrl);

    assert.calledWith(onSelectURL, validYouTubeUrl);
  });

  it('does not invoke `onSelectURL` if URL is not valid', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit('not-a-youtube-url');
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(errorMessage.text(), 'Please enter a YouTube URL');
  });

  it('invokes `onSelectURL` when submit button is clicked', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderPicker({ onSelectURL });

    wrapper.find('URLPickerForm').prop('inputRef').current.value =
      validYouTubeUrl;
    wrapper.update();

    wrapper.find('button[data-testid="submit-button"]').props().onClick();

    assert.calledWith(onSelectURL, validYouTubeUrl);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderPicker(),
    })
  );
});
