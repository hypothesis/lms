import { checkAccessibility, mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import StudentToolbar from '../StudentToolbar';

describe('StudentToolbar', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      studentToolbar: {
        assignmentCheckpointEnabled: true,
        courseCheckpointConfig: { revealed: false },
      },
    };
  });

  const render = (props = {}) =>
    mount(
      <Config.Provider value={fakeConfig}>
        <StudentToolbar {...props} />
      </Config.Provider>,
    );

  const status = wrapper =>
    wrapper.find('[data-testid="student-checkpoint-status"]');

  it('renders nothing when there is no student toolbar config', () => {
    delete fakeConfig.studentToolbar;
    assert.isFalse(status(render()).exists());
  });

  it('renders nothing when checkpoints are not enabled', () => {
    fakeConfig.studentToolbar.assignmentCheckpointEnabled = false;
    assert.isFalse(status(render()).exists());
  });

  it('renders nothing while waiting for sync', () => {
    assert.isFalse(status(render({ waitingForSync: true })).exists());
  });

  it('shows annotations as hidden when not revealed', () => {
    assert.include(status(render()).text(), 'Annotations are hidden');
  });

  it('defaults to hidden when no checkpoint config is present', () => {
    delete fakeConfig.studentToolbar.courseCheckpointConfig;
    assert.include(status(render()).text(), 'Annotations are hidden');
  });

  it('shows annotations as visible when revealed via course config', () => {
    fakeConfig.studentToolbar.courseCheckpointConfig = { revealed: true };
    assert.include(status(render()).text(), 'Annotations are visible');
  });

  it('prefers the sync checkpoint state over the course config', () => {
    const wrapper = render({
      syncCheckpoint: { revealed: true, revealDate: null },
    });
    assert.include(status(wrapper).text(), 'Annotations are visible');
  });

  it('does not render a due date when none is provided', () => {
    assert.isFalse(
      render().exists('[data-testid="student-checkpoint-due-date"]'),
    );
  });

  it('renders the due date when provided', () => {
    fakeConfig.studentToolbar.assignmentDueDate = '2026-07-01T10:00:00';
    assert.isTrue(
      render().exists('[data-testid="student-checkpoint-due-date"]'),
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => render(),
    }),
  );
});
