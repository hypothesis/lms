import { mount } from 'enzyme';

import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import LaunchErrorDialog, { $imports } from '../LaunchErrorDialog';

describe('LaunchErrorDialog', () => {
  let retryStub;

  function renderDialog(props) {
    return mount(
      <LaunchErrorDialog
        errorState="error-authorizing"
        busy={false}
        onRetry={retryStub}
        {...props}
      />
    );
  }

  beforeEach(() => {
    retryStub = sinon.stub();

    $imports.$mock(mockImportedComponents());

    // Un-mock `Dialog` so we can get a reference to the "Try again" button.
    $imports.$restore({
      './Dialog': true,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  [
    {
      errorState: 'error-authorizing',
      expectedText: 'Hypothesis needs your authorization',
      hasDetailedError: false,
      retryAction: 'Authorize',
    },
    {
      errorState: 'blackboard_file_not_found_in_course',
      expectedText: 'The file has been deleted from Blackboard',
    },
    {
      errorState: 'canvas_api_permission_error',
      expectedText: "Hypothesis couldn't get the assignment's file from Canvas",
    },
    {
      errorState: 'canvas_file_not_found_in_course',
      expectedText: 'edit the assignment and re-select the file',
    },
    {
      errorState: 'error-fetching',
      expectedText: 'There was a problem fetching this Hypothesis assignment',
    },
    {
      errorState: 'error-reporting-submission',
      expectedText: 'There was a problem submitting this Hypothesis assignment',
      retryAction: null,
    },
    {
      errorState: 'canvas_group_set_not_found',
      expectedText:
        "Assignment's group set no longer exists in CanvasHypothesis couldn't load this assignment because the assignment's group set no longer exists in Canvas.To fix this problem, an instructor needs to edit the assignment settings and select a new group set.",
      retryAction: null,
    },
    {
      errorState: 'canvas_group_set_empty',
      expectedText: 'The group set for this Hypothesis assignment is empty.',
      retryAction: null,
    },
    {
      errorState: 'canvas_student_not_in_group',
      expectedText:
        "You're not in any of this assignment's groupsHypothesis couldn't launch this assignment because you aren't in any of the groups in the assignment's group set.To fix the problem, an instructor needs to add your Canvas user account to one of this assignment's groups.",
      retryAction: null,
    },
  ].forEach(
    ({
      errorState,
      expectedText,
      hasDetailedError = true,
      retryAction = 'Try again',
    }) => {
      it(`displays expected error for "${errorState}" error state`, () => {
        const error = new Error('Detailed error info');

        const wrapper = renderDialog({ error, errorState });

        assert.include(wrapper.text(), expectedText);
        assert.equal(wrapper.exists('LabeledButton'), retryAction !== null);
        if (retryAction) {
          assert.include(wrapper.find('LabeledButton').text(), retryAction);
        }
        assert.equal(wrapper.exists('ErrorDisplay'), hasDetailedError);
      });
    }
  );

  it('only renders back-end messaging in "error-fetching" state, if provided', () => {
    // The presence of `errorMessage` on the errorLike object will prevent the
    // canned text from rendering
    const errorLike = {
      message: 'This is the JS error message',
      errorMessage: 'This is the back-end error message',
    };

    const wrapper = renderDialog({
      error: errorLike,
      errorState: 'error-fetching',
    });

    assert.notInclude(
      wrapper.text(),
      'There was a problem fetching this Hypothesis assignment'
    );
  });

  it('initiates retry when "Try again" button is clicked', () => {
    const wrapper = renderDialog();

    act(() => {
      wrapper.find('LabeledButton').prop('onClick')();
    });

    assert.called(retryStub);
  });

  it('enables "Try again" button if `busy` is false', () => {
    const wrapper = renderDialog({ busy: false });
    assert.isFalse(wrapper.find('LabeledButton').prop('disabled'));
  });

  it('disables "Try again" button if `busy` is true', () => {
    const wrapper = renderDialog({ busy: true });
    assert.isTrue(wrapper.find('LabeledButton').prop('disabled'));
  });

  it('shows error details', () => {
    const error = new Error('Oh no');
    const wrapper = renderDialog({
      errorState: 'canvas_api_permission_error',
      error,
    });
    assert.equal(wrapper.find('ErrorDisplay').prop('error'), error);
  });
});
