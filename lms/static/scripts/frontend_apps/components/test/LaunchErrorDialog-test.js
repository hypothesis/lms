import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../config';
import LaunchErrorDialog, { $imports } from '../LaunchErrorDialog';

describe('LaunchErrorDialog', () => {
  let retryStub;

  function renderDialog(props = {}, config = {}) {
    return mount(
      <Config.Provider value={config}>
        <LaunchErrorDialog
          errorState="error-authorizing"
          busy={false}
          onRetry={retryStub}
          {...props}
        />
      </Config.Provider>,
    );
  }

  // Custom mock for ErrorModal which includes `extraActions` in the output.
  function MockErrorModal({ children, extraActions }) {
    return (
      <>
        {children}
        {extraActions}
      </>
    );
  }
  MockErrorModal.displayName = 'ErrorModal';

  beforeEach(() => {
    retryStub = sinon.stub();

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      './ErrorModal': MockErrorModal,
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
      errorState: 'canvas_page_not_found_in_course',
      expectedText: 'The page has been deleted from Canvas',
      expectedTitle: "Hypothesis couldn't find the page in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'd2l_file_not_found_in_course_instructor',
      expectedText:
        'To fix the issue, recreate this assignment and select a different file.',
      expectedTitle: "Hypothesis couldn't find the file in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'd2l_file_not_found_in_course_student',
      expectedText:
        'Please ask the course instructor to review the settings of this assignment',
      expectedTitle: "Hypothesis couldn't find the file in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'moodle_file_not_found_in_course',
      expectedText:
        'To fix the issue an instructor needs to edit this assignment and select a different file.',
      expectedTitle: "Hypothesis couldn't find the file in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'moodle_page_not_found_in_course',
      expectedText: 'The page has been deleted from Moodle',
      expectedTitle: "Hypothesis couldn't find the page in the course",
      hasRetry: true,
      withError: true,
    },
    {
      errorState: 'canvas_group_set_not_found',
      expectedText:
        "Hypothesis couldn't find this assignment's group set. This could be because:The group set has been deleted from Canvas.This course was created by copying another course (Canvas doesn't copy the group sets over when you copy a course).",
      expectedTitle: 'Group set not found',
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
      errorState: 'd2l_group_set_not_found',
      expectedText:
        "Hypothesis couldn't load this assignment because the assignment's group category no longer exists.To fix this problem, an instructor needs to edit the assignment settings and select a new group category.",
      expectedTitle: "Assignment's group category no longer exists",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'moodle_group_set_not_found',
      expectedText:
        "Hypothesis couldn't load this assignment because the assignment's grouping no longer exists.To fix this problem, an instructor needs to edit the assignment settings and select a new grouping.",
      expectedTitle: "Assignment's grouping no longer exists",
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
      errorState: 'd2l_group_set_empty',
      expectedText:
        'The group category for this Hypothesis assignment is empty',
      expectedTitle: "Assignment's group category is empty",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'moodle_group_set_empty',
      expectedText: 'The grouping for this Hypothesis assignment is empty',
      expectedTitle: "Assignment's grouping is empty",
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
      errorState: 'd2l_student_not_in_group',
      expectedText:
        "you aren't in any of the groups in the assignment's group category",
      expectedTitle: "You're not in any of this assignment's groups",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'moodle_student_not_in_group',
      expectedText:
        "you aren't in any of the groups in the assignment's grouping",
      expectedTitle: "You're not in any of this assignment's groups",
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'vitalsource_user_not_found',
      expectedText: 'Hypothesis could not find your VitalSource user account',
      expectedTitle: 'VitalSource account not found',
      hasRetry: false,
      withError: true,
    },
    {
      errorState: 'vitalsource_no_book_license',
      expectedText: 'Your VitalSource library does not have this book in it',
      expectedTitle: 'Book not available',
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
    },
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
      'There was a problem fetching this Hypothesis assignment',
    );
  });

  it('forwards `busy` to `ErrorModal`', () => {
    const wrapper = renderDialog({ busy: true });
    assert.isTrue(wrapper.find('ErrorModal').prop('busy'));
  });

  it('does not show "Edit assignment" link if user is a student', () => {
    const wrapper = renderDialog();
    assert.isFalse(wrapper.exists('[data-testid="edit-link"]'));
  });

  it('shows "Edit assignment" link if user is an instructor', () => {
    const config = {
      instructorToolbar: {
        editingEnabled: true,
      },
    };
    const wrapper = renderDialog({}, config);
    const editLink = wrapper.find('Link[data-testid="edit-link"]');
    assert.isTrue(editLink.exists());
    assert.equal(editLink.prop('href'), '/app/content-item-selection');
  });
});
