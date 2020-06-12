import { createElement } from 'preact';
import { mount } from 'enzyme';

import Spinner from '../Spinner';

describe('Spinner', () => {
  it('renders a spinner', () => {
    const wrapper = mount(
      <Spinner className="loading-thingie" visible={true} />
    );
    assert.isTrue(wrapper.exists('SvgIcon.Spinner__svg')); // apply default styling to svg
    assert.isTrue(wrapper.exists('.loading-thingie')); // custom supplied class
    assert.isTrue(wrapper.exists('.Spinner--fade-in')); // visible is true
  });

  it('renders a spinner hidden', () => {
    const wrapper = mount(
      <Spinner className="loading-thingie" visible={false} />
    );
    assert.isFalse(wrapper.exists('.Spinner--fade-in'));
  });
});
