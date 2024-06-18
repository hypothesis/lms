import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../../config';
import DashboardApp, { $imports } from '../DashboardApp';

describe('DashboardApp', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      dashboard: {
        user: {
          display_name: 'John Doe',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <DashboardApp />
      </Config.Provider>,
    );
  }

  ['John Doe', 'Jane Doe', 'Foobar'].forEach(displayName => {
    it('shows expected username', () => {
      fakeConfig.dashboard.user.display_name = displayName;
      const wrapper = createComponent();

      assert.equal(
        wrapper.find('[data-testid="display-name"]').text(),
        displayName,
      );
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
