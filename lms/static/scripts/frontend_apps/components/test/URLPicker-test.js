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

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    })
  );
});
