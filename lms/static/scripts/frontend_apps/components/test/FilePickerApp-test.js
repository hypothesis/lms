import {
  checkAccessibility,
  mockImportedComponents,
  mount,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import FilePickerApp, {
  loadFilePickerConfig,
  $imports,
} from '../FilePickerApp';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

/**
 * Click the button in `wrapper` with a given `data-testid` attribute.
 */
function clickButton(wrapper, testId) {
  wrapper.find(`button[data-testid="${testId}"]`).simulate('click');
}

describe('FilePickerApp', () => {
  let fakeConfig;

  const renderFilePicker = (props = {}) => {
    const preventFormSubmission = e => e.preventDefault();
    return mount(
      <Config.Provider value={fakeConfig}>
        <FilePickerApp onSubmit={preventFormSubmission} {...props} />
      </Config.Provider>,
      {
        connected: true,
      },
    );
  };

  beforeEach(() => {
    fakeConfig = {
      api: { authToken: 'DUMMY_AUTH_TOKEN' },
      product: {
        settings: {
          groupsEnabled: false,
        },
      },
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
        promptForTitle: false,
        promptForGradable: false,
        assignmentTypes: ['reading'],
      },
    };

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  /**
   * Check that the expected hidden form fields were set.
   */
  function checkFormFields(
    wrapper,
    {
      content,
      groupSet = null,
      formFields = {},
      title = null,
      autoGradingConfig = null,
      checkpointEnabled = false,
    },
  ) {
    const fieldsComponent = wrapper.find('FilePickerFormFields');
    assert.deepEqual(fieldsComponent.props(), {
      children: [],
      content,
      formFields: { ...fakeConfig.filePicker.formFields, ...formFields },
      groupSet,
      title,
      autoGradingConfig,
      checkpointEnabled,
    });
  }

  function checkHiddenFormFields(wrapper, { fields = {} }) {
    const fieldsComponent = wrapper.find('HiddenFormFields');
    assert.deepEqual(fieldsComponent.props(), {
      children: [],
      fields: fields,
    });
  }

  function clickContinueButton(wrapper) {
    interact(wrapper, () => {
      wrapper.find('Button[data-testid="save-button"]').props().onClick();
    });
  }

  it('renders form with correct action', () => {
    const wrapper = renderFilePicker();
    const form = wrapper.find('form');
    assert.equal(form.prop('action'), 'https://www.shinylms.com/');
  });

  it('renders content selector when content has not yet been selected', () => {
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.exists('ContentSelector'));
  });

  describe('assignment-type workflow', () => {
    function clickNext(wrapper) {
      interact(wrapper, () => {
        wrapper
          .find('Button[data-testid="workflow-next-button"]')
          .props()
          .onClick();
      });
    }

    function clickBack(wrapper) {
      interact(wrapper, () => {
        wrapper
          .find('Button[data-testid="workflow-back-button"]')
          .props()
          .onClick();
      });
    }

    // Selecting a type advances the workflow immediately (no "Next" on the
    // first step).
    function selectAssignmentType(wrapper, type) {
      interact(wrapper, () => {
        wrapper.find('AssignmentTypeSelector').props().onSelect(type);
      });
    }

    function setDueDate(wrapper, date) {
      interact(wrapper, () => {
        wrapper.find('DueDateSelector').props().onChange(date);
      });
    }

    /**
     * Local `datetime-local` string (`YYYY-MM-DDTHH:MM`) `days` from now
     * (negative for the past).
     */
    function dueDateFromNow(days) {
      const date = new Date();
      date.setDate(date.getDate() + days);
      const pad = n => String(n).padStart(2, '0');
      return (
        `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
        `T${pad(date.getHours())}:${pad(date.getMinutes())}`
      );
    }

    it('does not show the workflow when only one type is available', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading'];
      const wrapper = renderFilePicker();

      assert.isFalse(wrapper.exists('AssignmentTypeSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('falls back to "reading" when no assignment types are provided', () => {
      fakeConfig.filePicker.assignmentTypes = undefined;
      const wrapper = renderFilePicker();

      // A single implicit "reading" type keeps the workflow dormant.
      assert.isFalse(wrapper.exists('AssignmentTypeSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('falls back to "reading" when the assignment types list is empty', () => {
      fakeConfig.filePicker.assignmentTypes = [];
      const wrapper = renderFilePicker();

      assert.isFalse(wrapper.exists('AssignmentTypeSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('shows the assignment-type step first when several types are available', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      assert.isTrue(wrapper.exists('AssignmentTypeSelector'));
      // The content selector is not shown until the workflow is complete.
      assert.isFalse(wrapper.exists('ContentSelector'));
    });

    it('skips to content selection for a "reading" assignment', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      selectAssignmentType(wrapper, 'reading');

      assert.isFalse(wrapper.exists('AssignmentTypeSelector'));
      assert.isFalse(wrapper.exists('CheckpointSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('walks through checkpoint and due-date steps for "Hide & Reveal"', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      // Selecting "hide_and_reveal" advances straight to the checkpoint step.
      selectAssignmentType(wrapper, 'hide_and_reveal');

      // Checkpoint step.
      assert.isTrue(wrapper.exists('CheckpointSelector'));
      assert.isFalse(wrapper.exists('ContentSelector'));
      clickNext(wrapper);

      // Due-date step.
      assert.isTrue(wrapper.exists('DueDateSelector'));
      assert.isFalse(wrapper.exists('ContentSelector'));
      clickNext(wrapper);

      // Regular flow takes over.
      assert.isFalse(wrapper.exists('DueDateSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('blocks the due-date step when the date is not in the future', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      clickNext(wrapper); // -> due-date
      assert.isTrue(wrapper.exists('DueDateSelector'));

      // A past date is rejected: navigation is blocked.
      setDueDate(wrapper, dueDateFromNow(-1));
      clickNext(wrapper);
      assert.isTrue(wrapper.exists('DueDateSelector'));
      assert.isFalse(wrapper.exists('ContentSelector'));
    });

    it('leaves the due-date step when the date is in the future', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      clickNext(wrapper); // -> due-date

      // A future date is accepted: the regular flow takes over.
      setDueDate(wrapper, dueDateFromNow(7));
      clickNext(wrapper);
      assert.isFalse(wrapper.exists('DueDateSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });

    it('does not offer a "Back" button on the first step', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      assert.isTrue(wrapper.exists('AssignmentTypeSelector'));
      assert.isFalse(
        wrapper.exists('Button[data-testid="workflow-back-button"]'),
      );
    });

    it('goes back through the "Hide & Reveal" steps', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      clickNext(wrapper); // -> due-date
      assert.isTrue(wrapper.exists('DueDateSelector'));

      clickBack(wrapper); // -> checkpoint
      assert.isTrue(wrapper.exists('CheckpointSelector'));
      assert.isFalse(wrapper.exists('DueDateSelector'));

      clickBack(wrapper); // -> assignment-type
      assert.isTrue(wrapper.exists('AssignmentTypeSelector'));
      assert.isFalse(wrapper.exists('CheckpointSelector'));
    });

    it('shows a step-specific card title', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();
      const cardTitle = () => wrapper.find('CardHeader').prop('title');

      // Assignment-type step.
      assert.equal(cardTitle(), 'Assignment mode');

      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      assert.equal(cardTitle(), 'Guided Social Annotation');

      clickNext(wrapper); // -> due-date
      assert.equal(cardTitle(), 'Guided Social Annotation');

      clickNext(wrapper); // -> regular flow
      assert.equal(cardTitle(), 'Assignment details');
    });

    it('returns to the assignment-type step via the header close button', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      // The mode-selection step itself offers no close button.
      assert.isNotOk(wrapper.find('CardHeader').prop('onClose'));

      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      clickNext(wrapper); // -> due-date
      assert.isTrue(wrapper.exists('DueDateSelector'));

      // The header exposes a close handler during the Guided sub-steps.
      const onClose = wrapper.find('CardHeader').prop('onClose');
      assert.isFunction(onClose);
      interact(wrapper, () => onClose());

      assert.isTrue(wrapper.exists('AssignmentTypeSelector'));
      assert.isFalse(wrapper.exists('DueDateSelector'));
    });

    it('recomputes the branch when the type is changed after going back', () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      // Enter the Hide & Reveal branch...
      selectAssignmentType(wrapper, 'hide_and_reveal'); // -> checkpoint
      clickBack(wrapper); // -> assignment-type

      // ...then switch to a regular reading assignment.
      selectAssignmentType(wrapper, 'reading'); // -> done (skips checkpoint/due-date)

      assert.isFalse(wrapper.exists('CheckpointSelector'));
      assert.isFalse(wrapper.exists('DueDateSelector'));
      assert.isTrue(wrapper.exists('ContentSelector'));
    });
  });

  function selectContent(wrapper, content) {
    const picker = wrapper.find('ContentSelector');
    interact(wrapper, () => {
      picker.props().onSelectContent(
        typeof content === 'string'
          ? {
              type: 'url',
              url: content,
            }
          : content,
      );
    });
  }

  function selectGroupConfig(
    wrapper,
    { useGroupSet = false, groupSet = null },
  ) {
    const groupSelector = wrapper.find('GroupConfigSelector');
    interact(wrapper, () => {
      groupSelector.props().onChangeGroupConfig({
        useGroupSet,
        groupSet,
      });
    });
  }

  context('when only content needs to be selected', () => {
    it('submits form when content is selected', () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      assert.called(onSubmit);
      checkFormFields(wrapper, {
        content: {
          type: 'url',
          url: 'https://example.com',
        },
      });
    });

    it('shows activity indicator when form is submitted', () => {
      const wrapper = renderFilePicker();
      assert.isFalse(wrapper.exists('SpinnerOverlay'));

      selectContent(wrapper, 'https://example.com');

      assert.isTrue(wrapper.exists('SpinnerOverlay'));
    });
  });

  context('when deepLinkingAPI is present', () => {
    const deepLinkingAPIPath = '/lti/1.3/deep_linking/form_fields';
    const deepLinkingAPIData = { some: 'data' };
    let fakeAPICall;
    let fakeFormFields;

    beforeEach(() => {
      fakeConfig.filePicker.deepLinkingAPI = {
        path: deepLinkingAPIPath,
        data: deepLinkingAPIData,
      };

      fakeAPICall = sinon.stub();
      fakeFormFields = { JWT: 'JWT VALUE' };

      fakeAPICall
        .withArgs(sinon.match({ path: deepLinkingAPIPath }))
        .resolves(fakeFormFields);

      $imports.$mock({
        '../utils/api': { apiCall: fakeAPICall },
      });
    });

    it('fetches form field values via deep linking API when content is selected', async () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      await waitFor(() => fakeAPICall.called);
      assert.calledWith(fakeAPICall, {
        authToken: 'DUMMY_AUTH_TOKEN',
        path: deepLinkingAPIPath,
        data: {
          ...deepLinkingAPIData,
          content: { type: 'url', url: 'https://example.com' },
          title: null,
          group_set: null,
          auto_grading_config: null,
          assignment_gradable_max_points: null,
          checkpoint_enabled: false,
          due_date: null,
        },
      });

      await waitFor(() => onSubmit.called, 100);

      wrapper.update();
      checkHiddenFormFields(wrapper, {
        fields: fakeFormFields,
      });
    });

    it('includes the selected group set in the deep linking API data', async () => {
      fakeConfig.product.settings.groupsEnabled = true;
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, { useGroupSet: true, groupSet: 'groupSet1' });
      clickContinueButton(wrapper);

      await waitFor(() => fakeAPICall.called);
      assert.calledWith(fakeAPICall, {
        authToken: 'DUMMY_AUTH_TOKEN',
        path: deepLinkingAPIPath,
        data: {
          ...deepLinkingAPIData,
          content: { type: 'url', url: 'https://example.com' },
          title: null,
          group_set: 'groupSet1',
          auto_grading_config: null,
          assignment_gradable_max_points: null,
          checkpoint_enabled: false,
          due_date: null,
        },
      });
    });

    it('sends the due date as a UTC datetime for "Hide & Reveal"', async () => {
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      const clickNext = () =>
        interact(wrapper, () => {
          wrapper
            .find('Button[data-testid="workflow-next-button"]')
            .props()
            .onClick();
        });

      // Walk the Hide & Reveal workflow, picking a future due date. The picker
      // value is local wall-clock time; the backend receives it as UTC.
      interact(wrapper, () => {
        // Selecting the type advances straight to the checkpoint step.
        wrapper
          .find('AssignmentTypeSelector')
          .props()
          .onSelect('hide_and_reveal');
      });
      clickNext(); // -> due-date
      const localDueDate = '2035-01-15T10:30';
      interact(wrapper, () => {
        wrapper.find('DueDateSelector').props().onChange(localDueDate);
      });
      clickNext(); // -> content selection

      selectContent(wrapper, 'https://example.com');

      await waitFor(() => fakeAPICall.called);
      assert.calledWith(fakeAPICall, {
        authToken: 'DUMMY_AUTH_TOKEN',
        path: deepLinkingAPIPath,
        data: {
          ...deepLinkingAPIData,
          content: { type: 'url', url: 'https://example.com' },
          title: null,
          group_set: null,
          auto_grading_config: null,
          assignment_gradable_max_points: null,
          checkpoint_enabled: true,
          due_date: new Date(localDueDate).toISOString(),
        },
      });
    });

    it('fetches form field values via deep linking API on implicit form submission', async () => {
      // Enable title field, which is a field where the user could trigger an
      // implicit submission by pressing Enter.
      fakeConfig.filePicker.promptForTitle = true;

      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      // Simulate implicit form submission, as if pressing Enter in title field.
      wrapper.find('form').getDOMNode().requestSubmit();

      await waitFor(() => fakeAPICall.called);
      await waitFor(() => onSubmit.called);
    });

    it('ignores implicit form submission when the form cannot be submitted', () => {
      // A group set is required but none is selected, so `canSubmit` is false.
      fakeConfig.product.settings.groupsEnabled = true;

      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, { useGroupSet: true, groupSet: null });

      // Simulate implicit form submission, as if pressing Enter.
      wrapper.find('form').getDOMNode().requestSubmit();

      // Nothing is submitted while the form is incomplete.
      assert.notCalled(fakeAPICall);
    });

    it('shows an error if the deepLinkingAPI call fails', async () => {
      const error = new Error('Something happened');
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      fakeAPICall
        .withArgs(sinon.match({ path: deepLinkingAPIPath }))
        .rejects(error);

      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      await waitForElement(wrapper, 'ErrorModal');

      const errDialog = wrapper.find('ErrorModal');
      assert.equal(errDialog.length, 1);
      assert.equal(errDialog.prop('error'), error);
    });
  });

  [
    {
      initConfig: () => (fakeConfig.product.settings.groupsEnabled = true),
    },
    {
      initConfig: () => (fakeConfig.filePicker.promptForTitle = true),
    },
  ].forEach(({ initConfig }) => {
    it('does not auto-submit form if details screen is enabled', () => {
      initConfig();

      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      assert.notCalled(onSubmit);
    });
  });

  context('when details screen is enabled', () => {
    beforeEach(() => {
      fakeConfig.product.settings.groupsEnabled = true;
    });

    [
      {
        content: 'https://example.com',
        summary: 'https://example.com',
      },
      {
        content: {
          type: 'url',
          name: 'Super-cali-fragi-listic.pdf',
          url: 'https://could.be.anything.com/really.pdf',
        },
        summary: 'Super-cali-fragi-listic.pdf',
      },
      {
        content: {
          type: 'url',
          url: 'blackboard://content-resource/_8615_1/',
        },
        summary: 'PDF file in Blackboard',
      },
      {
        content: {
          type: 'url',
          url: 'canvas-studio://media/5',
        },
        summary: 'Video in Canvas Studio',
      },
      {
        content: {
          type: 'url',
          url: 'd2l://file/course/123/file_id/456',
        },
        summary: 'PDF file in D2L',
      },
      {
        content: { type: 'url', url: 'canvas://file/ID' },
        summary: 'PDF file in Canvas',
      },
      {
        content: { type: 'url', url: 'vitalsource://bookID/BOOK/cfi/CFI' },
        summary: 'Book from VitalSource',
      },
      {
        content: { type: 'url', url: 'jstor://1234' },
        summary: 'JSTOR article',
      },
    ].forEach(({ content, summary }) => {
      it('displays a summary of the assignment content', () => {
        const wrapper = renderFilePicker();

        selectContent(wrapper, content);

        assert.equal(
          wrapper.find('[data-testid="content-summary"]').text(),
          summary,
        );
      });
    });

    it('truncates long URLs in assignment content summary', () => {
      const wrapper = renderFilePicker();

      selectContent(
        wrapper,
        'https://en.wikipedia.org/wiki/Cannonball_Baker_Sea-To-Shining-Sea_Memorial_Trophy_Dash',
      );

      assert.equal(
        wrapper.find('[data-testid="content-summary"]').text(),
        'en.wikipedia.org/…/Cannonball_Baker_Sea-To-Shinin…',
      );
    });

    it('disables "Continue" button when group sets are enabled but no group set is selected', () => {
      const wrapper = renderFilePicker();

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, { useGroupSet: true, groupSet: null });

      assert.isTrue(
        wrapper.find('Button[data-testid="save-button"]').prop('disabled'),
      );
    });

    describe('when `promptForTitle` is enabled', () => {
      beforeEach(() => {
        fakeConfig.filePicker.promptForTitle = true;
      });

      it('displays "Title" input on details screen', () => {
        const wrapper = renderFilePicker();
        selectContent(wrapper, 'https://example.com');
        const titleInput = wrapper.find('input[data-testid="title-input"]');
        assert.isTrue(titleInput.exists());
        assert.equal(titleInput.getDOMNode().value, 'Hypothesis assignment');
      });

      it('includes title when submitting form', () => {
        const wrapper = renderFilePicker();
        selectContent(wrapper, 'https://example.com');

        const titleInput = wrapper.find('input[data-testid="title-input"]');
        titleInput.getDOMNode().value = 'Example assignment';
        titleInput.simulate('input');

        const formFields = wrapper.find('FilePickerFormFields');
        assert.equal(formFields.prop('title'), 'Example assignment');
      });
    });

    [true, false].forEach(useGroupSet => {
      it('submits form when "Continue" button is clicked', () => {
        const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
        const wrapper = renderFilePicker({ onSubmit });

        selectContent(wrapper, 'https://example.com');
        selectGroupConfig(wrapper, { useGroupSet, groupSet: 'groupSet1' });

        assert.notCalled(onSubmit);
        clickContinueButton(wrapper);

        assert.called(onSubmit);
        checkFormFields(wrapper, {
          content: {
            type: 'url',
            url: 'https://example.com',
          },
          groupSet: useGroupSet ? 'groupSet1' : null,
        });
      });
    });

    it('initializes auto_grading_config if assignment already has it', () => {
      const autoGradingConfig = {
        grading_type: 'scaled',
        activity_calculation: 'separate',
        required_annotations: 10,
        required_replies: 5,
      };
      const url = 'https://example.com';

      fakeConfig.assignment = {
        auto_grading_config: autoGradingConfig,
        document: { url },
      };
      fakeConfig.filePicker.autoGradingEnabled = true;

      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      checkFormFields(wrapper, {
        content: { type: 'url', url },
        autoGradingConfig,
      });
    });

    it('does not submit form when "Continue" is clicked if there are validation errors', () => {
      fakeConfig.filePicker.promptForTitle = true;

      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      // Make an input on the details screen invalid.
      const titleInput = wrapper
        .find('input[data-testid="title-input"]')
        .getDOMNode();
      titleInput.value = '';

      clickContinueButton(wrapper);
      assert.notCalled(onSubmit);

      titleInput.value = 'No longer empty';
      clickContinueButton(wrapper);

      assert.called(onSubmit);
    });

    it('shows activity indicator when form is submitted', () => {
      const wrapper = renderFilePicker();
      assert.isFalse(wrapper.exists('FullScreenSpinner'));

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, {
        useGroupSet: true,
        groupSet: 'groupSet1',
      });
      interact(wrapper, () => {
        wrapper.find('Button[children="Continue"]').props().onClick();
      });

      assert.isTrue(wrapper.exists('SpinnerOverlay'));
    });
  });

  it('shows error dialog if an error occurs while selecting content', () => {
    const wrapper = renderFilePicker();
    const error = new Error('Something went wrong');

    interact(wrapper, () => {
      wrapper.find('ContentSelector').prop('onError')({
        title: 'Something went wrong',
        error,
      });
    });

    const errDialog = wrapper.find('ErrorModal');
    assert.equal(errDialog.length, 1);
    assert.equal(errDialog.prop('error'), error);
  });

  it('dismisses error dialog if user clicks close button', () => {
    const error = new Error('Failed to load');
    const wrapper = renderFilePicker();

    interact(wrapper, () => {
      wrapper.find('ContentSelector').prop('onError')({
        title: 'Something went wrong',
        error,
      });
    });

    const errDialog = wrapper.find('ErrorModal');
    const onCancel = errDialog.prop('onCancel');
    assert.isFunction(onCancel);
    interact(wrapper, onCancel);
    assert.isFalse(wrapper.exists('ErrorModal'));
  });

  context('when promptForGradable is enabled', () => {
    const deepLinkingAPIPath = '/lti/1.3/deep_linking/form_fields';
    const deepLinkingAPIData = { some: 'data' };
    let fakeAPICall;
    let fakeFormFields;

    beforeEach(() => {
      fakeConfig.filePicker.deepLinkingAPI = {
        path: deepLinkingAPIPath,
        data: deepLinkingAPIData,
      };
      fakeConfig.filePicker.promptForGradable = true;

      fakeAPICall = sinon.stub();
      fakeFormFields = { JWT: 'JWT VALUE' };

      fakeAPICall
        .withArgs(sinon.match({ path: deepLinkingAPIPath }))
        .resolves(fakeFormFields);

      $imports.$mock({
        '../utils/api': { apiCall: fakeAPICall },
      });
    });

    [true, false].forEach(promptForGradable => {
      it('displays "max points" input on details screen when promptForGradable is enabled', () => {
        fakeConfig.filePicker.promptForGradable = promptForGradable;

        const wrapper = renderFilePicker();
        selectContent(wrapper, 'https://example.com');
        const gradableCheckbox = wrapper.find(
          'input[data-testid="gradable-max-input"]',
        );

        assert.equal(gradableCheckbox.exists(), promptForGradable);
      });
    });

    it('includes max points when submitting form', async () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });
      selectContent(wrapper, 'https://example.com');

      const pointsInput = wrapper.find(
        'input[data-testid="gradable-max-input"]',
      );
      pointsInput.getDOMNode().value = '10';
      pointsInput.simulate('change');

      clickContinueButton(wrapper);

      await waitFor(() => fakeAPICall.called);
      assert.calledWith(fakeAPICall, {
        authToken: 'DUMMY_AUTH_TOKEN',
        path: deepLinkingAPIPath,
        data: {
          ...deepLinkingAPIData,
          content: { type: 'url', url: 'https://example.com' },
          title: null,
          group_set: null,
          auto_grading_config: null,
          assignment_gradable_max_points: 10,
          checkpoint_enabled: false,
          due_date: null,
        },
      });

      await waitFor(() => onSubmit.called);

      wrapper.update();
      checkHiddenFormFields(wrapper, {
        fields: fakeFormFields,
      });
    });

    it('submits null when empty', async () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      clickContinueButton(wrapper);

      await waitFor(() => fakeAPICall.called);
      assert.calledWith(fakeAPICall, {
        authToken: 'DUMMY_AUTH_TOKEN',
        path: deepLinkingAPIPath,
        data: {
          ...deepLinkingAPIData,
          content: { type: 'url', url: 'https://example.com' },
          title: null,
          group_set: null,
          auto_grading_config: null,
          assignment_gradable_max_points: null,
          checkpoint_enabled: false,
          due_date: null,
        },
      });
    });

    it('opens popover when clicking info button', async () => {
      const wrapper = renderFilePicker();

      selectContent(wrapper, 'https://example.com');
      clickContinueButton(wrapper);
      await waitFor(() => fakeAPICall.called);

      assert.isFalse(wrapper.find('Popover').prop('open'));
      wrapper.find('IconButton').props().onClick();
      wrapper.update();
      assert.isTrue(wrapper.find('Popover').prop('open'));

      wrapper.find('Popover').props().onClose();
      wrapper.update();
      assert.isFalse(wrapper.find('Popover').prop('open'));
    });
  });

  context('when editing an existing assignment', () => {
    beforeEach(() => {
      fakeConfig.assignment = {
        document: {
          url: 'https://test.com/example.pdf',
        },
      };
    });

    it('shows "Back to assignment" link', () => {
      const wrapper = renderFilePicker();
      assert.isTrue(wrapper.exists('[data-testid="back-link"]'));
    });

    it('shows description of existing content and "Change" button', () => {
      const wrapper = renderFilePicker();
      const description = wrapper.find('[data-testid="content-summary"]');
      assert.equal(description.text(), 'https://test.com/example.pdf');
      assert.isTrue(wrapper.exists('button[data-testid="edit-content"]'));
    });

    it('shows "Save" button instead of "Continue" button', () => {
      const wrapper = renderFilePicker();
      const saveButton = wrapper.find('button[data-testid="save-button"]');
      assert.equal(saveButton.text(), 'Save');
    });

    it('skips the assignment-type workflow when editing', () => {
      // The assignment mode (reading vs. "Hide & Reveal") is chosen only at
      // creation, so editing goes straight to the assignment content/details
      // even when several types are available.
      fakeConfig.filePicker.assignmentTypes = ['reading', 'hide_and_reveal'];
      const wrapper = renderFilePicker();

      assert.isFalse(wrapper.exists('AssignmentTypeSelector'));
      assert.isFalse(wrapper.exists('CheckpointSelector'));
      assert.isFalse(wrapper.exists('DueDateSelector'));
      assert.isTrue(wrapper.exists('[data-testid="content-summary"]'));
    });

    [true, false].forEach(groupsEnabled => {
      it('allows editing content selection', () => {
        fakeConfig.product.settings.groupsEnabled = groupsEnabled;
        const wrapper = renderFilePicker();

        // Initially the content selector form is not visible.
        assert.isFalse(wrapper.exists('ContentSelector'));

        // Clicking on the change/edit button next to the content description
        // should show the content selector.
        clickButton(wrapper, 'edit-content');
        const contentSelector = wrapper.find('ContentSelector');
        assert.isTrue(contentSelector.exists());
        assert.deepEqual(contentSelector.prop('initialContent'), {
          type: 'url',
          url: 'https://test.com/example.pdf',
        });

        // Selecting new content should revert back to showing the content
        // description.
        act(() => {
          contentSelector.prop('onSelectContent')({
            type: 'url',
            url: 'https://othersite.com/test.pdf',
          });
        });
        wrapper.update();
        assert.isFalse(wrapper.exists('ContentSelector'));
        const description = wrapper.find('[data-testid="content-summary"]');
        assert.equal(description.text(), 'https://othersite.com/test.pdf');
      });

      it('displays group config selector when groups are enabled', () => {
        fakeConfig.product.settings.groupsEnabled = groupsEnabled;
        const wrapper = renderFilePicker();

        assert.equal(wrapper.exists('GroupConfigSelector'), groupsEnabled);
      });
    });

    it('cancels editing content when clicking "Cancel" button', () => {
      const wrapper = renderFilePicker();
      clickButton(wrapper, 'edit-content');
      clickButton(wrapper, 'cancel-edit-content');
      assert.isFalse(wrapper.exists('ContentSelector'));
    });

    [true, false].forEach(autoGradingEnabled => {
      it('displays auto grading configurator when it is enabled', () => {
        fakeConfig.filePicker.autoGradingEnabled = autoGradingEnabled;
        const wrapper = renderFilePicker();

        assert.equal(
          wrapper.exists('AutoGradingConfigurator'),
          autoGradingEnabled,
        );
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    }),
  );
});

describe('loadFilePickerConfig', () => {
  let fakeAPICall;
  beforeEach(() => {
    fakeAPICall = sinon.stub().resolves({});

    $imports.$mock({
      '../utils/api': {
        apiCall: fakeAPICall,
      },
    });
  });

  it('rejects if `editing` config is missing', async () => {
    let error;
    try {
      await loadFilePickerConfig({});
    } catch (e) {
      error = e;
    }
    assert.instanceOf(error, Error);
    assert.equal(error.message, 'Assignment editing config missing');
  });

  it('fetches `filePicker` config from API', async () => {
    const config = {
      api: {
        authToken: 'token',
      },
      editing: {
        getConfig: { path: '/assignments/edit', data: { foo: 'bar' } },
      },
    };
    const assignment = {};
    const filePicker = {};
    fakeAPICall.resolves({ assignment, filePicker });

    const updatedConfig = await loadFilePickerConfig(config);

    assert.calledWith(
      fakeAPICall,
      sinon.match({
        authToken: config.api.authToken,
        path: '/assignments/edit',
        data: config.editing.getConfig.data,
      }),
    );
    assert.deepEqual(updatedConfig, {
      ...config,
      assignment,
      filePicker,
    });
  });
});
