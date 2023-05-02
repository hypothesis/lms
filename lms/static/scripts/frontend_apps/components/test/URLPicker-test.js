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
      wrapper.find('UrlPickerForm').prop('defaultURL'),
      'https://arxiv.org/pdf/1234.pdf'
    );
  });

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({
      onSelectURL,
      defaultURL: 'https://example.com/foo',
    });

    wrapper.find('UrlPickerForm').props().onSubmit();

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('does not invoke `onSelectURL` if URL is not valid', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL, defaultURL: 'not-a-url' });

    wrapper.find('UrlPickerForm').props().onSubmit();
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(errorMessage.text(), 'Please enter a URL');
  });

  it('does not invoke `onSelectURL` if URL is for a non-http(s) protocol', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({
      onSelectURL,
      defaultURL: 'ftp:///warez.fun',
    });

    wrapper.find('UrlPickerForm').props().onSubmit();
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'Please use a URL that starts with "http" or "https"'
    );
  });

  it('shows an additional error message if URL is for a local file', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({
      onSelectURL,
      defaultURL: 'file:///my/local.pdf',
    });

    wrapper.find('UrlPickerForm').props().onSubmit();
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
