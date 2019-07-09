import { createElement } from 'preact';
import ErrorDialog from '../ErrorDialog';
import ErrorDisplay from '../ErrorDisplay';

import { shallow } from 'enzyme';

describe('ErrorDialog', () => {
  it('displays details of the error', () => {
    const err = new Error('Something went wrong');
    const wrapper = shallow(<ErrorDialog title="Oh no!" error={err} />);

    assert.include(wrapper.find(ErrorDisplay).props(), {
      message: 'Oh no!',
      error: err,
    });
  });
});
