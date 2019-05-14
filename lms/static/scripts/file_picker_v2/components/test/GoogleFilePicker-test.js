import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import GoogleFilePicker, { $imports } from '../GoogleFilePicker';

describe('GoogleFilePicker', () => {
  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ children }) => <Fragment>{children}</Fragment>;

  const renderGooglePicker = (props = {}) =>
    mount(<GoogleFilePicker {...props} />);

  beforeEach(() => {
    $imports.$mock({
      './Dialog': FakeDialog,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('shows a placeholder message', () => {
    const wrapper = renderGooglePicker();
    assert.match(wrapper.debug(), /not yet implemented/);
  });
});
