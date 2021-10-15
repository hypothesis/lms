import { mount } from 'enzyme';

import URLPicker from '../URLPicker';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('URLPicker', () => {
  const renderUrlPicker = (props = {}) => mount(<URLPicker {...props} />);

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'https://example.com/foo';

    wrapper.find('LabeledButton').props().onClick(new Event('click'));

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('does not invoke `onSelectURL` if URL is not valid', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'not-a-url';

    wrapper.find('LabeledButton').props().onClick(new Event('click'));
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('[data-testid="error-message"]');
    assert.isTrue(errorMessage.exists());
    assert.include(errorMessage.text(), 'Please enter a URL');
  });

  it('does not invoke `onSelectURL` if URL is for a non-http(s) protocol', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'ftp:///warez.fun';

    wrapper.find('LabeledButton').props().onClick(new Event('click'));
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

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'file:///my/local.pdf';

    wrapper.find('LabeledButton').props().onClick(new Event('click'));
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
