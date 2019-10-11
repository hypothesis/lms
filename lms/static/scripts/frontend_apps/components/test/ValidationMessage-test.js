import { createElement } from 'preact';
import { shallow } from 'enzyme';

import ValidationMessage from '../ValidationMessage';

describe('ValidationMessage', () => {
  const renderMessage = (props = {}) => {
    return shallow(<ValidationMessage {...props} />);
  };

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
    wrapper.simulate('click');
    assert.isTrue(onCloseProp.calledOnce);
    assert.isTrue(wrapper.find('.ValidationMessage--closed').exists());
    //assert.equal(wrapper.text(), 'some error');
  });
});
