import { mount } from 'enzyme';

import ValidationMessage, { $imports } from '../ValidationMessage';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('ValidationMessage', () => {
  const renderMessage = (props = {}) => {
    return mount(<ValidationMessage message="Test message" {...props} />);
  };

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders closed by default', () => {
    const wrapper = renderMessage();
    assert.isTrue(wrapper.find('[data-testid="message-closed"]').exists());
    assert.equal(wrapper.find('input').prop('tabIndex'), '-1');
  });

  it('renders open when passing `open=true` prop', () => {
    const wrapper = renderMessage({ open: true });
    assert.isTrue(wrapper.find('[data-testid="message-open"]').exists());
    assert.equal(wrapper.find('input').prop('tabIndex'), '0');
  });

  it('sets the message from the `message` prop', () => {
    const wrapper = renderMessage({ message: 'some error' });
    assert.equal(wrapper.find('input').props().value, 'some error');
  });

  it('closes the message and calls `onClose` prop when clicked', () => {
    const onCloseProp = sinon.stub();
    const wrapper = renderMessage({
      onClose: onCloseProp,
      open: true,
      message: 'foo',
    });
    wrapper.find('input').simulate('click');
    assert.isTrue(onCloseProp.calledOnce);
    assert.isTrue(wrapper.find('[data-testid="message-closed"]').exists());
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'closed',
        content: () => renderMessage(),
      },
      {
        name: 'open',
        content: () => renderMessage({ open: true }),
      },
    ])
  );
});
