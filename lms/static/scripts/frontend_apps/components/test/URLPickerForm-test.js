import { mount } from 'enzyme';
import { createRef } from 'preact';

import { checkAccessibility } from '../../../test-util/accessibility';
import URLPickerForm from '../URLPickerForm';

describe('URLPicker', () => {
  const renderUrlPicker = (props = {}) => mount(<URLPickerForm {...props} />);

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderUrlPicker({
      defaultURL: 'https://arxiv.org/pdf/1234.pdf',
    });
    assert.equal(
      wrapper.find('input').getDOMNode().value,
      'https://arxiv.org/pdf/1234.pdf'
    );
  });

  it('invokes `onSubmit` when user submits a URL', () => {
    const onSubmit = sinon.stub();
    const inputRef = createRef();
    const wrapper = renderUrlPicker({ onSubmit, inputRef });

    wrapper.find('input').getDOMNode().value = 'the-url';
    wrapper.update();

    wrapper.find('form').props().onSubmit(new Event('click'));

    assert.calledWith(onSubmit, 'the-url');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    })
  );
});
