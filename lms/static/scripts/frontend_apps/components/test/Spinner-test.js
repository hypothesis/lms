import { mount } from 'enzyme';

import Spinner from '../Spinner';

describe('Spinner', () => {
  it('renders a spinner', () => {
    const wrapper = mount(<Spinner className="loading-thingie" />);
    assert.isTrue(wrapper.exists('SvgIcon.loading-thingie'));
  });
});
