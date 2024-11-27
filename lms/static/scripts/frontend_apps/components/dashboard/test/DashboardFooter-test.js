import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import DashboardFooter from '../DashboardFooter';

describe('DashboardFooter', () => {
  function createComponent() {
    return mount(<DashboardFooter />);
  }

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
