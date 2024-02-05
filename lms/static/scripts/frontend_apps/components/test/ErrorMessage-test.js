import { mount } from 'enzyme';

import ErrorMessage from '../ErrorMessage';

describe('ErrorMessage', () => {
  function createErrorMessage(props = {}) {
    return mount(<ErrorMessage {...props} />);
  }

  [null, undefined, 'error message', false, 45].forEach(error => {
    it('renders error only if it has a truthy value', () => {
      const wrapper = createErrorMessage({ error });
      assert.equal(wrapper.exists('UIMessage'), !!error);
    });
  });
});
