import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';
import { Config } from '../../config';
import InstructorToolbar, { $imports } from '../InstructorToolbar';

describe('InstructorToolbar', () => {
  let fakeConfig;
  let fakeGrading;

  beforeEach(() => {
    fakeGrading = {
      enabled: true,
      courseName: 'course name',
      assignmentName: 'course assignment',
    };
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      grading: fakeGrading,
    };

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderToolbar = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <InstructorToolbar {...props} />
      </Config.Provider>
    );
  };

  it('does not render assignment info when grading config is not set', () => {
    delete fakeConfig.grading;

    const wrapper = renderToolbar();
    assert.equal(wrapper.find('[data-testid="assignment-name"]').length, 0);
  });

  it('does not render assignment info when grading is not enabled', () => {
    fakeGrading.enabled = false;

    const wrapper = renderToolbar();
    assert.equal(wrapper.find('[data-testid="assignment-name"]').length, 0);
  });

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
