import { mount } from 'enzyme';
import { createElement } from 'preact';

import FullScreenSpinner from '../FullScreenSpinner';

describe('FullScreenSpinner', () => {
  // There is no logic in this component, so this is just a basic "make sure it
  // doesn't crash" test.
  it('renders', () => {
    mount(<FullScreenSpinner />);
  });
});
