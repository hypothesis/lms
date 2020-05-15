import { createElement } from 'preact';
import { mount } from 'enzyme';

import Spinner from '../Spinner';

describe('Spinner', () => {
  it('renders a spinner', () => {
    const wrapper = mount(<Spinner className="loading-thingie" />);
    assert.isTrue(wrapper.exists('SvgIcon.loading-thingie:not("is-hidden")'));
  });

  it('renders a spinner hidden', () => {
    const wrapper = mount(<Spinner hide={true} className="loading-thingie" />);
    assert.isFalse(wrapper.exists('SvgIcon'));
  });
});
