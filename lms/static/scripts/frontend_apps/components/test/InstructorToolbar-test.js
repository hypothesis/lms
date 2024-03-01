import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../config';
import InstructorToolbar, { $imports } from '../InstructorToolbar';

describe('InstructorToolbar', () => {
  let fakeConfig;
  let fakeInstructorToolbar;

  beforeEach(() => {
    fakeInstructorToolbar = {
      editingEnabled: false,
      gradingEnabled: false,
      courseName: 'course name',
      assignmentName: 'course assignment',
    };
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      instructorToolbar: fakeInstructorToolbar,
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
      </Config.Provider>,
    );
  };

  it('does not render assignment info when config is not set', () => {
    delete fakeConfig.instructorToolbar;

    const wrapper = renderToolbar();
    assert.equal(wrapper.find('[data-testid="assignment-name"]').length, 0);
  });

  it('does not render edit button if editing assignments is disabled', () => {
    fakeInstructorToolbar.editingEnabled = false;
    const wrapper = renderToolbar();
    assert.isFalse(wrapper.exists('[data-testid="edit"]'));
  });

  it('renders edit button if editing assignments is enabled', () => {
    fakeInstructorToolbar.editingEnabled = true;
    const wrapper = renderToolbar();
    assert.isTrue(wrapper.exists('[data-testid="edit"]'));
  });

  [true, false, undefined].forEach(acceptComments => {
    it('renders grading controls when grading is enabled', () => {
      fakeInstructorToolbar.gradingEnabled = true;
      fakeInstructorToolbar.students = [];
      fakeInstructorToolbar.acceptGradingComments = acceptComments;

      const wrapper = renderToolbar();
      const gradingControls = wrapper.find('GradingControls');

      assert.isTrue(gradingControls.exists());
      assert.equal(gradingControls.prop('acceptComments'), acceptComments);
    });
  });

  it('does not render grading controls when grading is not enabled', () => {
    const wrapper = renderToolbar();
    assert.isFalse(wrapper.exists('GradingControls'));
  });

  it('sets the assignment and course names', () => {
    const wrapper = renderToolbar();
    assert.equal(
      wrapper.find('[data-testid="assignment-name"]').text(),
      'course assignment',
    );
    assert.equal(
      wrapper.find('[data-testid="course-name"]').text(),
      'course name',
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderToolbar(),
    }),
  );
});
