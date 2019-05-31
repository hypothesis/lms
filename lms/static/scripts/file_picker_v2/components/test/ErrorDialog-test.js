import { createElement } from 'preact';
import ErrorDialog from '../ErrorDialog';

import { shallow } from 'enzyme';

describe('ErrorDialog', () => {
  it('displays details of the error', () => {
    const err = new Error('Something went wrong');
    const wrapper = shallow(<ErrorDialog title="Oh no!" error={err} />);
    assert.include(wrapper.debug(), 'Something went wrong');
  });
});
