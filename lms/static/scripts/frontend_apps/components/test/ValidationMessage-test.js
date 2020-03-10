import { createElement } from 'preact';
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
    assert.isTrue(wrapper.find('.ValidationMessage--closed').exists());
  });

  it('renders open when passing `open=true` prop', () => {
    const wrapper = renderMessage({ open: true });
    assert.isTrue(wrapper.find('.ValidationMessage--open').exists());
  });

  it('sets the message from the `message` prop', () => {
    const wrapper = renderMessage({ message: 'some error' });
    assert.equal(wrapper.text(), 'some error');
  });

  it('closes the message and calls `onClose` prop when clicked', () => {
    const onCloseProp = sinon.stub();
    const wrapper = renderMessage({
      onClose: onCloseProp,
      open: true,
      message: 'foo',
    });
    wrapper.find('button').simulate('click');
    assert.isTrue(onCloseProp.calledOnce);
    assert.isTrue(wrapper.find('.ValidationMessage--closed').exists());
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
