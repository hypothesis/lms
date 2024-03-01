import {
  checkAccessibility,
  mockImportedComponents,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { GradingService, withServices } from '../../services';
import SubmitGradeForm, { $imports } from '../SubmitGradeForm';

describe('SubmitGradeForm', () => {
  const fakeStudent = {
    userid: 'student1',
    displayName: 'Student 1',
    LISResultSourcedId: 1,
    LISOutcomeServiceUrl: '',
  };

  const fakeStudentAlt = {
    userid: 'student2',
    displayName: 'Student 2',
    LISResultSourcedId: 2,
    LISOutcomeServiceUrl: '',
  };

  let fakeGradingService;

  const fakeUseWarnOnPageUnload = sinon.stub();

  const SubmitGradeFormWrapper = withServices(SubmitGradeForm, () => [
    [GradingService, fakeGradingService],
  ]);

  let container;
  const renderForm = (props = {}) => {
    return mount(<SubmitGradeFormWrapper student={fakeStudent} {...props} />, {
      attachTo: container,
    });
  };

  const inputSelector = 'input[data-testid="grade-input"]';

  async function waitForGradeFetch(wrapper) {
    await waitFor(() => {
      wrapper.update();
      return !wrapper.find('Spinner').exists();
    });
    wrapper.update();
  }

  beforeEach(() => {
    // This extra element is necessary to test automatic `focus`-ing
    // of the component's `input` element
    container = document.createElement('div');
    document.body.appendChild(container);

    // Reset the api grade stubs for each test because
    // some tests below will change these for specific cases.
    fakeGradingService = fakeGradingService = {
      submitGrade: sinon.stub().resolves({}),
      fetchGrade: sinon.stub().resolves({
        currentScore: 1,
        comment: 'Good job!',
      }),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/use-warn-on-page-unload': {
        useWarnOnPageUnload: fakeUseWarnOnPageUnload,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('does not disable the input field when the disable prop is missing', () => {
    const wrapper = renderForm();
    assert.isFalse(wrapper.find(inputSelector).prop('disabled'));
  });

  it('disables the submit button when the `student` prop is `null`', () => {
    const wrapper = renderForm({ student: null });
    assert.isTrue(wrapper.find('button[type="submit"]').prop('disabled'));
  });

  it("sets the input key to the student's LISResultSourcedId", () => {
    const wrapper = renderForm();
    assert.equal(wrapper.find('Input').key(), fakeStudent.LISResultSourcedId);
  });

  it('clears out the previous grade when changing students', async () => {
    const wrapper = renderForm();
    await waitForGradeFetch(wrapper);

    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '10');
    wrapper.setProps({ student: fakeStudentAlt });
    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '');
  });

  it('clears the displayed grade value if the currently-focused student has an empty grade', async () => {
    const wrapper = renderForm();

    await waitForGradeFetch(wrapper);
    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '10');

    fakeGradingService.fetchGrade.resolves({ currentScore: null });
    wrapper.setProps({ student: fakeStudentAlt });
    await waitForGradeFetch(wrapper);

    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '');
  });

  it("displays a focused-student's grade if it is 0 (zero)", async () => {
    fakeGradingService.fetchGrade.resolves({ currentScore: 0 });
    const wrapper = renderForm();

    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '');

    await waitForGradeFetch(wrapper);

    assert.strictEqual(wrapper.find(inputSelector).prop('value'), '0');
  });

  it('focuses the input field when changing students and fetching the grade', async () => {
    document.body.focus();
    const wrapper = renderForm();

    await waitForGradeFetch(wrapper);

    wrapper.setProps({ student: fakeStudentAlt });

    await waitForGradeFetch(wrapper);

    assert.equal(
      document.activeElement.getAttribute('data-testid'),
      'grade-input',
    );
  });

  [5, 10, 20, 100, undefined].forEach(scoreMaximum => {
    it("selects the input field's text when changing students and fetching the grade", async () => {
      document.body.focus();
      const wrapper = renderForm({ scoreMaximum });

      await waitForGradeFetch(wrapper);

      wrapper.setProps({ student: fakeStudentAlt });

      await waitForGradeFetch(wrapper);

      assert.equal(document.getSelection().toString(), `${scoreMaximum ?? 10}`);
    });
  });

  // Enter a grade and submit the form.
  function submitGrade(wrapper, gradeValue = 5) {
    wrapper.find('input[data-testid="grade-input"]').getDOMNode().value =
      gradeValue.toString();

    act(() => {
      // nb. `wrapper.simulate('click')` unfortunately doesn't submit forms.
      wrapper.find('button[data-testid="submit-button"]').getDOMNode().click();
    });

    wrapper.update();
  }

  context('when submitting a grade', () => {
    it('shows a loading spinner when submitting a grade', async () => {
      const wrapper = renderForm();
      await waitForGradeFetch(wrapper);

      submitGrade(wrapper);
      assert.isTrue(wrapper.find('SpinnerOverlay').exists());
    });

    it('shows the error dialog when the grade request throws an error', async () => {
      const wrapper = renderForm();
      const error = {
        serverMessage: 'message',
        details: 'details',
      };
      fakeGradingService.submitGrade.rejects(error);

      await waitForGradeFetch(wrapper);
      submitGrade(wrapper);

      const errorModal = await waitForElement(wrapper, 'ErrorModal');
      // Ensure the error object passed to ErrorDialog is the same as the one thrown
      assert.equal(errorModal.prop('error'), error);

      // Error message should be hidden when its close action is triggered.
      wrapper.find('ErrorModal').invoke('onCancel')();
      assert.isFalse(wrapper.exists('ErrorModal'));
    });

    it('sets the success animation class when the grade has posted', async () => {
      const wrapper = renderForm();
      await waitForGradeFetch(wrapper);

      submitGrade(wrapper);
      await waitForGradeFetch(wrapper);

      assert.isTrue(
        wrapper.find(inputSelector).hasClass('animate-gradeSubmitSuccess'),
      );
    });

    it('removes the success animation class after keyboard input', async () => {
      const wrapper = renderForm();

      await waitForGradeFetch(wrapper);
      submitGrade(wrapper);

      await waitForGradeFetch(wrapper);

      wrapper.find(inputSelector).simulate('input');
      assert.isFalse(
        wrapper.find(inputSelector).hasClass('animate-gradeSubmitSuccess'),
      );
    });

    it('closes the spinner after the grade has posted', async () => {
      const wrapper = renderForm();

      await waitForGradeFetch(wrapper);
      submitGrade(wrapper);

      await waitFor(() => {
        wrapper.update();
        return !wrapper.exists('FullScreenSpinner');
      });
    });

    [
      { gradeValue: 10, expectedGrade: 1 },
      { gradeValue: 5.5, expectedGrade: 0.55 },
      { gradeValue: 2, expectedGrade: 0.2 },
    ].forEach(({ gradeValue, expectedGrade }) => {
      it('calls grading service with right grade', () => {
        const wrapper = renderForm();

        submitGrade(wrapper, gradeValue);

        assert.calledWith(fakeGradingService.submitGrade, {
          student: fakeStudent,
          grade: expectedGrade,
          comment: undefined,
        });
      });
    });

    it('throws if the value is not a number', async () => {
      const wrapper = renderForm();

      let error;
      try {
        await wrapper
          .find('form')
          .props()
          .onSubmit({ preventDefault: sinon.stub() });
      } catch (e) {
        error = e;
      }

      assert.instanceOf(error, Error);
      assert.equal(error.message, 'New grade "" is not a number');
    });
  });

  context('when fetching a grade', () => {
    it('sets the defaultValue prop to an empty string if the grade is falsey', async () => {
      fakeGradingService.fetchGrade.resolves({ currentScore: null });
      const wrapper = renderForm();

      await waitForGradeFetch(wrapper);

      assert.strictEqual(wrapper.find(inputSelector).prop('value'), '');
    });

    it('shows the error dialog when the grade request throws an error', async () => {
      const error = {
        serverMessage: 'message',
        details: 'details',
      };
      fakeGradingService.fetchGrade.rejects(error);
      const wrapper = renderForm();

      await waitForGradeFetch(wrapper);

      assert.isTrue(wrapper.find('ErrorModal').exists());
      // Ensure the error object passed to ErrorDialog is the same as the one thrown
      assert.equal(wrapper.find('ErrorModal').prop('error'), error);

      // Error message should be hidden when its close action is triggered.
      wrapper.find('ErrorModal').invoke('onCancel')();
      assert.isFalse(wrapper.exists('ErrorModal'));
    });

    it("sets the input defaultValue prop to the student's grade", async () => {
      const wrapper = renderForm();
      await waitForGradeFetch(wrapper);
      // note, grade is scaled by 10
      assert.strictEqual(wrapper.find(inputSelector).prop('value'), '10');
    });

    it('hides the Spinner after the grade is fetched', async () => {
      const wrapper = renderForm();
      await waitForGradeFetch(wrapper);
      assert.isFalse(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find('Spinner')
          .exists(),
      );
    });
  });

  context('when there are unsaved changes', () => {
    // Default new value to something different from the original grade
    const changeGrade = (wrapper, newValue = 8) => {
      wrapper.find(inputSelector).getDOMNode().value = `${newValue}`;
      wrapper.find(inputSelector).simulate('input');
    };

    it('will warn on page unload', () => {
      const wrapper = renderForm();

      assert.calledWith(fakeUseWarnOnPageUnload.lastCall, false);
      changeGrade(wrapper);
      assert.calledWith(fakeUseWarnOnPageUnload.lastCall, true);
    });

    it('will notify onUnsavedChanges', async () => {
      const fakeOnUnsavedChanges = sinon.stub();
      const wrapper = renderForm({ onUnsavedChanges: fakeOnUnsavedChanges });

      await waitForGradeFetch(wrapper);

      changeGrade(wrapper);
      assert.calledWith(fakeOnUnsavedChanges.lastCall, true);

      // Changing back to the original grade should notify there are no unsaved changes
      changeGrade(wrapper, 10);
      assert.calledWith(fakeOnUnsavedChanges.lastCall, false);
    });
  });

  context('when comments are accepted', () => {
    const changeComment = (wrapper, newComment) => {
      wrapper
        .find('GradingCommentButton')
        .props()
        .onInput({
          target: {
            value: newComment,
          },
        });
      wrapper.update();
    };
    const submitForm = wrapper =>
      wrapper.find('GradingCommentButton').props().onSubmit();

    [true, false].forEach(acceptComments => {
      it('renders GradingCommentButton', () => {
        const wrapper = renderForm({ acceptComments });
        assert.equal(acceptComments, wrapper.exists('GradingCommentButton'));
      });
    });

    it('submits grade using internal popover submit button', async () => {
      const wrapper = renderForm({ acceptComments: true });

      await waitForGradeFetch(wrapper);

      // If we submit with no changes, the originally loaded comment will be sent
      submitForm(wrapper);
      assert.calledWith(fakeGradingService.submitGrade.lastCall, {
        student: fakeStudent,
        grade: 1,
        comment: 'Good job!',
      });

      // If we change the comment and submit again, the new comment will be sent
      changeComment(wrapper, 'Something else');
      submitForm(wrapper);
      assert.calledWith(fakeGradingService.submitGrade.lastCall, {
        student: fakeStudent,
        grade: 1,
        comment: 'Something else',
      });
    });

    it('does not submit grade if form has invalid values', async () => {
      const wrapper = renderForm({ acceptComments: true });

      await waitForGradeFetch(wrapper);

      // Set an invalid grade value and submit form via comment button
      wrapper.find(inputSelector).getDOMNode().value = 'not a number';
      wrapper.update();
      submitForm(wrapper);

      assert.notCalled(fakeGradingService.submitGrade);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility(
      {
        content: () => renderForm(),
      },
      {
        name: 'when disabled',
        content: () => renderForm({ disabled: true }),
      },
    ),
  );
});
