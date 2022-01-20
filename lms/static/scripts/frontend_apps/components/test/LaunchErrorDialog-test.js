import { mount } from 'enzyme';

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
      expectedTitle: 'Authorize Hypothesis',
      hasRetry: true,
      retryAction: 'Authorize',
      withError: false,
    },
    {
      errorState: 'blackboard_file_not_found_in_course',
      expectedText: 'The file has been deleted from Blackboard',
      expectedTitle: "Hypothesis couldn't find the file in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'canvas_api_permission_error',
      expectedText: "Hypothesis couldn't get the assignment's file from Canvas",
      expectedTitle: "Couldn't get the file from Canvas",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'canvas_file_not_found_in_course',
      expectedText: 'edit the assignment and re-select the file',
      expectedTitle: "Hypothesis couldn't find the file in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'canvas_group_set_not_found',
      expectedText:
        "Hypothesis couldn't load this assignment because the assignment's group set no longer exists.To fix this problem, an instructor needs to edit the assignment settings and select a new group set.",
      expectedTitle: "Assignment's group set no longer exists",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'blackboard_group_set_not_found',
      expectedText:
        "Hypothesis couldn't load this assignment because the assignment's group set no longer exists.To fix this problem, an instructor needs to edit the assignment settings and select a new group set.",
      expectedTitle: "Assignment's group set no longer exists",
      hasRetry: false,
      withError: true,
    },

    {
      errorState: 'blackboard_group_set_empty',
      expectedText: 'The group set for this Hypothesis assignment is empty',
      expectedTitle: "Assignment's group set is empty",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'canvas_group_set_empty',
      expectedText: 'The group set for this Hypothesis assignment is empty',
      expectedTitle: "Assignment's group set is empty",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'blackboard_student_not_in_group',
      expectedText: 'an instructor needs to add your Blackboard user',
      expectedTitle: "You're not in any of this assignment's groups",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'canvas_student_not_in_group',
      expectedText:
        "you aren't in any of the groups in the assignment's group set",
      expectedTitle: "You're not in any of this assignment's groups",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'error-fetching',
      expectedText: 'There was a problem fetching this Hypothesis assignment',
      expectedTitle: 'Something went wrong',
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'error-reporting-submission',
      expectedText: 'There was a problem submitting this Hypothesis assignment',
      expectedTitle: 'Something went wrong',
      hasRetry: false,
      withError: true,
    },
  ].forEach(
    ({
      errorState,
      expectedText,
      expectedTitle,
      hasRetry = false,
      withError = true,
      retryAction,
    }) => {
      it(`displays expected error for "${errorState}" error state`, () => {
        const error = new Error('Detailed error info');
        const wrapper = renderDialog({ error, errorState: errorState });

        const modalProps = wrapper.find('ErrorModal').props();
        assert.include(wrapper.find('ErrorModal').text(), expectedText);
        assert.equal(modalProps.title, expectedTitle);
        assert.equal(modalProps.retryLabel, retryAction);
        if (hasRetry) {
          assert.equal(modalProps.onRetry, retryStub);
        } else {
          assert.isUndefined(modalProps.onRetry);
        }
        if (retryAction) {
          assert.equal(modalProps.retryLabel, retryAction);
        }
        if (!withError) {
          assert.isUndefined(modalProps.error);
        }
      });
    }
  );

  it('only renders back-end messaging in "error-fetching" state, if provided', () => {
    // The presence of `serverMessage` on the errorLike object will prevent the
    // canned text from rendering
    const errorLike = {
      message: 'This is the JS error message',
      serverMessage: 'This is the back-end error message',
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

  it('forwards `busy` to `ErrorModal`', () => {
    const wrapper = renderDialog({ busy: true });
    assert.isTrue(wrapper.find('ErrorModal').prop('busy'));
  });
});
