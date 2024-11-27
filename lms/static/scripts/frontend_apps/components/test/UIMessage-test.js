import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import UIMessage from '../UIMessage';

describe('UIMessage', () => {
  const renderComponent = (props = {}) =>
    mount(<UIMessage {...props}>This is a message</UIMessage>);

  it('renders a checkmark next to success messages', () => {
    const wrapper = renderComponent({ status: 'success' });
    assert.isTrue(wrapper.find('[data-testid="uimessage-icon"]').exists());
    assert.isTrue(wrapper.find('CheckIcon').exists());
  });

  it('renders a cancel icon next to error messages', () => {
    const wrapper = renderComponent({ status: 'error' });
    assert.isTrue(wrapper.find('[data-testid="uimessage-icon"]').exists());
    assert.isTrue(wrapper.find('CancelIcon').exists());
  });

  it('does not render an icon next to info messages', () => {
    const wrapper = renderComponent();
    assert.isFalse(wrapper.find('[data-testid="uimessage-icon"]').exists());
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderComponent(),
    }),
  );
});
