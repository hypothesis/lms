import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import UrlPickerForm from '../UrlPickerForm';

describe('URLPicker', () => {
  const renderUrlPicker = (props = {}) => mount(<UrlPickerForm {...props} />);

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
    const wrapper = renderUrlPicker({ onSubmit });

    wrapper.find('form').props().onSubmit(new Event('click'));

    assert.called(onSubmit);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    })
  );
});
