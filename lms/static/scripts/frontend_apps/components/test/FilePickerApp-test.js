/* eslint-disable new-cap */

import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

import { Config } from '../../config';
import FilePickerApp, { $imports } from '../FilePickerApp';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitFor } from '../../../test-util/wait';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

describe('FilePickerApp', () => {
  let container;
  let fakeConfig;

  const renderFilePicker = (props = {}) => {
    const preventFormSubmission = e => e.preventDefault();
    return mount(
      <Config.Provider value={fakeConfig}>
        <FilePickerApp onSubmit={preventFormSubmission} {...props} />
      </Config.Provider>,
      {
        attachTo: container,
      }
    );
  };

  beforeEach(() => {
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
        canvas: {
          groupsEnabled: false,
          ltiLaunchUrl: 'https://lms.anno.co/lti_launch',
        },
      },
    };

    container = document.createElement('div');
    document.body.appendChild(container);

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
    container.remove();
  });

  /**
   * Check that the expected hidden form fields were set.
   */
  function checkFormFields(
    wrapper,
    expectedContent,
    expectedGroupSet,
    expectedExtLTIAssignmentId
  ) {
    const formFields = wrapper.find('FilePickerFormFields');
    assert.deepEqual(formFields.props(), {
      children: [],
      content: expectedContent,
      formFields: fakeConfig.filePicker.formFields,
      extLTIAssignmentId: expectedExtLTIAssignmentId,
      groupSet: expectedGroupSet,
      ltiLaunchURL: fakeConfig.filePicker.canvas.ltiLaunchUrl,
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

  function selectContent(wrapper, content) {
    const picker = wrapper.find('ContentSelector');
    interact(wrapper, () => {
      picker.props().onSelectContent(
        typeof content === 'string'
          ? {
              type: 'url',
              url: content,
            }
          : content
      );
    });
  }

  function selectGroupConfig(
    wrapper,
    { useGroupSet = false, groupSet = null }
  ) {
    const groupSelector = wrapper.find('GroupConfigSelector');
    interact(wrapper, () => {
      groupSelector.props().onChangeGroupConfig({
        useGroupSet,
        groupSet,
      });
    });
  }

  context('when create assignment configuration is enabled', () => {
    const authURL = 'https://testlms.hypothes.is/authorize';
    const createAssignmentPath = '/api/canvas/assignments';
    let fakeAPICall;
    let fakeNewAssignment;

    beforeEach(() => {
      fakeConfig.filePicker.createAssignmentAPI = {
        authURL,
        path: createAssignmentPath,
      };

      fakeAPICall = sinon.stub();
      fakeNewAssignment = { ext_lti_assignment_id: 10 };

      fakeAPICall
        .withArgs(sinon.match({ path: createAssignmentPath }))
        .resolves(fakeNewAssignment);

      $imports.$mock({
        '../utils/api': { apiCall: fakeAPICall },
      });
    });

    it('calls backend api when content is selected', async () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      await waitFor(() => fakeAPICall.called);
      wrapper.update();

      assert.calledWith(fakeAPICall, {
        authToken: 'dummyAuthToken',
        path: createAssignmentPath,
        data: {
          content: { type: 'url', url: 'https://example.com' },
          groupset: null,
        },
      });

      assert.called(onSubmit);
      checkFormFields(
        wrapper,
        {
          type: 'url',
          url: 'https://example.com',
        },
        null /* groupSet */,
        fakeNewAssignment.ext_lti_assignment_id
      );
    });

    it('shows an error if creating the assignment fails', async () => {
      const error = new Error('Something happened');
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      fakeAPICall
        .withArgs(sinon.match({ path: createAssignmentPath }))
        .rejects(error);

      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      await waitFor(() => fakeAPICall.called);
      wrapper.update();

      const errDialog = wrapper.find('ErrorDialog');
      assert.equal(errDialog.length, 1);
      assert.equal(errDialog.prop('error'), error);
    });
  });
  context('when groups are not enabled', () => {
    it('submits form when content is selected', () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      assert.called(onSubmit);
      checkFormFields(
        wrapper,
        {
          type: 'url',
          url: 'https://example.com',
        },
        null /* groupSet */,
        null /* extLTIAssignmentId */
      );
    });

    it('shows activity indicator when form is submitted', () => {
      const wrapper = renderFilePicker();
      assert.isFalse(wrapper.exists('FullScreenSpinner'));

      selectContent(wrapper, 'https://example.com');

      assert.isTrue(wrapper.exists('FullScreenSpinner'));
    });
  });

  context('when group configuration is enabled', () => {
    beforeEach(() => {
      fakeConfig.filePicker.canvas.groupsEnabled = true;
    });

    it('does not submit form when content is selected', () => {
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      selectContent(wrapper, 'https://example.com');

      assert.notCalled(onSubmit);
    });

    [
      {
        content: 'https://example.com',
        summary: 'https://example.com',
      },
      {
        content: { type: 'file', id: 'abcd' },
        summary: 'PDF file in Canvas',
      },
      {
        content: { type: 'vitalsource', bookID: 'abc', cfi: '/1/2' },
        summary: 'Book from VitalSource',
      },
    ].forEach(({ content, summary }) => {
      it('displays a summary of the assignment content', () => {
        const wrapper = renderFilePicker();

        selectContent(wrapper, content);

        assert.equal(
          wrapper.find('[data-testid="content-summary"]').text(),
          summary
        );
      });
    });

    it('truncates long URLs in assignment content summary', () => {
      const wrapper = renderFilePicker();

      selectContent(
        wrapper,
        'https://en.wikipedia.org/wiki/Cannonball_Baker_Sea-To-Shining-Sea_Memorial_Trophy_Dash'
      );

      assert.equal(
        wrapper.find('[data-testid="content-summary"]').text(),
        'en.wikipedia.org/…/Cannonball_Baker_Sea-To-Shining-Sea_Memorial_…'
      );
    });

    it('disables "Continue" button when group sets are enabled but no group set is selected', () => {
      const wrapper = renderFilePicker();

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, { useGroupSet: true, groupSet: null });

      assert.isTrue(
        wrapper.find('LabeledButton[children="Continue"]').prop('disabled')
      );
    });

    [true, false].forEach(useGroupSet => {
      it('submits form when "Continue" button is clicked', () => {
        const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
        const wrapper = renderFilePicker({ onSubmit });

        selectContent(wrapper, 'https://example.com');
        selectGroupConfig(wrapper, { useGroupSet, groupSet: 'groupSet1' });

        assert.notCalled(onSubmit);
        interact(wrapper, () => {
          wrapper.find('LabeledButton[children="Continue"]').props().onClick();
        });

        assert.called(onSubmit);
        checkFormFields(
          wrapper,
          {
            type: 'url',
            url: 'https://example.com',
          },
          useGroupSet ? 'groupSet1' : null,
          null /* extLTIAssignmentId */
        );
      });
    });

    it('shows activity indicator when form is submitted', () => {
      const wrapper = renderFilePicker();
      assert.isFalse(wrapper.exists('FullScreenSpinner'));

      selectContent(wrapper, 'https://example.com');
      selectGroupConfig(wrapper, { useGroupSet: true, groupSet: 'groupSet1' });
      interact(wrapper, () => {
        wrapper.find('LabeledButton[children="Continue"]').props().onClick();
      });

      assert.isTrue(wrapper.exists('FullScreenSpinner'));
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

    const errDialog = wrapper.find('ErrorDialog');
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

    const errDialog = wrapper.find('ErrorDialog');
    const onCancel = errDialog.prop('onCancel');
    assert.isFunction(onCancel);
    interact(wrapper, onCancel);
    assert.isFalse(wrapper.exists('ErrorDialog'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    })
  );
});
