import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import Button from '../Button';
import URLPicker, { $imports } from '../URLPicker';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('URLPicker', () => {
  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ buttons, children }) => (
    <Fragment>
      {buttons} {children}
    </Fragment>
  );
  const renderUrlPicker = (props = {}) => mount(<URLPicker {...props} />);

  beforeEach(() => {
    $imports.$mock({
      './Dialog': FakeDialog,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'https://example.com/foo';

    wrapper.find(Button).props().onClick(new Event('click'));
    wrapper.update();

    assert.isFalse(wrapper.find('ValidationMessage').exists());
    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('shows the validation message if a URL is not entered', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find(Button).props().onClick(new Event('click'));
    wrapper.update();

    assert.isTrue(wrapper.find('ValidationMessage').exists());
    assert.equal(wrapper.find('ValidationMessage').prop('open'), true);
    assert.equal(
      wrapper.find('ValidationMessage').prop('message'),
      'A valid URL is required'
    );
  });

  it('dismisses the validation message on user input', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find(Button).props().onClick(new Event('click'));
    wrapper.update();
    assert.isTrue(wrapper.find('ValidationMessage').exists());
    assert.equal(wrapper.find('ValidationMessage').prop('open'), true);

    wrapper.find('input[name="path"]').simulate('input');
    assert.equal(wrapper.find('ValidationMessage').prop('open'), false);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    })
  );
});
