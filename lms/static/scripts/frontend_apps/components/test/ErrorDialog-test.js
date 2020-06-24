import { createElement } from 'preact';
import { mount } from 'enzyme';

import ErrorDialog, { $imports } from '../ErrorDialog';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('ErrorDialog', () => {
  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('displays details of the error', () => {
    const err = new Error('Something went wrong');
    const wrapper = mount(<ErrorDialog title="Oh no!" error={err} />);

    assert.include(wrapper.find('ErrorDisplay').props(), {
      message: 'Oh no!',
      error: err,
    });
  });

  it('passes the `size` prop to the Dialog', () => {
    const err = new Error('Something went wrong');
    const sizes = { width: 100, height: 100 };
    const wrapper = mount(
      <ErrorDialog title="Oh no!" error={err} size={sizes} />
    );
    assert.equal(wrapper.find('Dialog').prop('size'), sizes);
  });
});
