import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

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

  const courseCheckpointConfig = {
    revealed: false,
    revealDate: null,
    revealUrl: '/api/assignments/1/checkpoint/reveal',
  };

  it('does not render the checkpoint bar when checkpoints are disabled', () => {
    fakeInstructorToolbar.assignmentCheckpointEnabled = false;
    fakeInstructorToolbar.courseCheckpointConfig = courseCheckpointConfig;
    assert.isFalse(renderToolbar().exists('CheckpointBar'));
  });

  it('does not render the checkpoint bar without checkpoint config', () => {
    // Without `courseCheckpointConfig` there is no reveal URL, so the bar (and
    // its reveal button) must not render.
    fakeInstructorToolbar.assignmentCheckpointEnabled = true;
    assert.isFalse(renderToolbar().exists('CheckpointBar'));
  });

  it('does not render the checkpoint bar while waiting for sync', () => {
    fakeInstructorToolbar.assignmentCheckpointEnabled = true;
    fakeInstructorToolbar.courseCheckpointConfig = courseCheckpointConfig;
    assert.isFalse(
      renderToolbar({ syncComplete: false }).exists('CheckpointBar'),
    );
  });

  it('renders the checkpoint bar with the course config', () => {
    fakeInstructorToolbar.assignmentCheckpointEnabled = true;
    fakeInstructorToolbar.courseCheckpointConfig = courseCheckpointConfig;
    fakeInstructorToolbar.assignmentDueDate = '2026-07-01T10:00:00';

    const bar = renderToolbar({ syncComplete: true }).find('CheckpointBar');
    assert.isTrue(bar.exists());
    assert.deepEqual(bar.prop('checkpoint'), courseCheckpointConfig);
    assert.equal(bar.prop('dueDate'), '2026-07-01T10:00:00');
  });

  it('prefers the sync checkpoint state over the course config', () => {
    fakeInstructorToolbar.assignmentCheckpointEnabled = true;
    fakeInstructorToolbar.courseCheckpointConfig = courseCheckpointConfig;

    const bar = renderToolbar({
      syncComplete: true,
      syncCheckpoint: { revealed: true, revealDate: '2026-07-05T10:00:00' },
    }).find('CheckpointBar');
    assert.deepEqual(bar.prop('checkpoint'), {
      revealed: true,
      revealDate: '2026-07-05T10:00:00',
      revealUrl: courseCheckpointConfig.revealUrl,
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderToolbar(),
    }),
  );
});
