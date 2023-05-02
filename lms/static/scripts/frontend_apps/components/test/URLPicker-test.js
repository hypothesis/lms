import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import URLPicker from '../URLPicker';

describe('URLPicker', () => {
  const renderUrlPicker = (props = {}) => mount(<URLPicker {...props} />);

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderUrlPicker({
      defaultURL: 'https://arxiv.org/pdf/1234.pdf',
    });
    assert.equal(
      wrapper.find('URLPickerForm').prop('defaultURL'),
      'https://arxiv.org/pdf/1234.pdf'
    );
  });

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit('https://example.com/foo');

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('does not invoke `onSelectURL` if URL is not valid', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit('not-a-url');
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(errorMessage.text(), 'Please enter a URL');
  });

  it('does not invoke `onSelectURL` if URL is for a non-http(s) protocol', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit('ftp:///warez.fun');
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'Please use a URL that starts with "http" or "https"'
    );
  });

  it('invokes `onSelectURL` when submit button is clicked', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });

    wrapper.find('URLPickerForm').prop('inputRef').current.value =
      'https://example.com/foo';
    wrapper.update();

    wrapper.find('button[data-testid="submit-button"]').props().onClick();

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('shows an additional error message if URL is for a local file', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });

    wrapper.find('URLPickerForm').props().onSubmit('file:///my/local.pdf');
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'URLs that start with "file" are files on your own computer.'
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    })
  );
});
