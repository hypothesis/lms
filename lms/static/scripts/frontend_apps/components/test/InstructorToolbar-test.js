import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';
import { Config } from '../../config';
import InstructorToolbar, { $imports } from '../InstructorToolbar';

describe('InstructorToolbar', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
    };

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderToolbar = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <InstructorToolbar
          courseName={'course name'}
          assignmentName={'course assignment'}
          {...props}
        />
      </Config.Provider>
    );
  };

  it('sets the assignment and course names', () => {
    const wrapper = renderToolbar();
    assert.equal(
      wrapper.find('[data-testid="assignment-name"]').text(),
      'course assignment'
    );
    assert.equal(
      wrapper.find('[data-testid="course-name"]').text(),
      'course name'
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderToolbar(),
    })
  );
});
