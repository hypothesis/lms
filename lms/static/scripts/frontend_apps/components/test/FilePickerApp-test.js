/* eslint-disable new-cap */
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitFor, waitForElement } from '../../../test-util/wait';
import { Config } from '../../config';
import FilePickerApp, {
  loadFilePickerConfig,
  $imports,
} from '../FilePickerApp';

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
      api: { authToken: 'DUMMY_AUTH_TOKEN' },
      product: {
        settings: {
          groupsEnabled: false,
        },
      },
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
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
    extraFormFields = {}
  ) {
    const formFields = wrapper.find('FilePickerFormFields');
    assert.deepEqual(formFields.props(), {
      children: [],
      content: expectedContent,
      formFields: { ...fakeConfig.filePicker.formFields, ...extraFormFields },
      groupSet: expectedGroupSet,
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
        null /* groupSet */
      );
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
          extra_params: { group_set: null },
        },
      });

      await waitFor(() => onSubmit.called, 100);

      wrapper.update();
      checkFormFields(
        wrapper,
        {
          type: 'url',
          url: 'https://example.com',
        },
        null /* groupSet */,
        fakeFormFields
      );
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

  context('when group configuration is enabled', () => {
    beforeEach(() => {
      fakeConfig.product.settings.groupsEnabled = true;
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
          url: 'd2l://file/course/123/file_id/456',
        },
        summary: 'PDF file in D2L',
      },

      {
        content: { type: 'file', id: 'abcd' },
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
        wrapper.find('Button[data-testid="save-button"]').prop('disabled')
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
          wrapper.find('Button[data-testid="save-button"]').props().onClick();
        });

        assert.called(onSubmit);
        checkFormFields(
          wrapper,
          {
            type: 'url',
            url: 'https://example.com',
          },
          useGroupSet ? 'groupSet1' : null
        );
      });
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

  context('when editing an existing assignment', () => {
    beforeEach(() => {
      fakeConfig.assignment = {
        document: {
          url: 'https://test.com/example.pdf',
        },
      };

      // FIXME - The existing assignment configuration and "Save" buttons
      // should be visible even if groups are not enabled.
      fakeConfig.product.settings.groupsEnabled = true;
    });

    /** Click the button to edit the existing content selection. */
    function clickEditButton(wrapper) {
      const editButton = wrapper.find('Button[data-testid="edit-content"]');
      assert.isTrue(editButton.exists());
      act(() => {
        editButton.prop('onClick')();
      });
      wrapper.update();
    }

    /** Click the button to cancel editing the content selection. */
    function clickCancelEditButton(wrapper) {
      const cancelButton = wrapper.find(
        'Button[data-testid="cancel-edit-content"]'
      );
      assert.isTrue(cancelButton.exists());
      act(() => {
        cancelButton.prop('onClick')();
      });
      wrapper.update();
    }

    it('shows "Back to assignment" link', () => {
      const wrapper = renderFilePicker();
      assert.isTrue(wrapper.exists('[data-testid="back-link"]'));
    });

    it('shows description of existing content and "Change" button', () => {
      const wrapper = renderFilePicker();
      const description = wrapper.find('[data-testid="content-summary"]');
      assert.equal(description.text(), 'https://test.com/example.pdf');
      assert.isTrue(wrapper.exists('Button[data-testid="edit-content"]'));
    });

    it('shows "Save" button instead of "Continue" button', () => {
      const wrapper = renderFilePicker();
      const saveButton = wrapper.find('Button[data-testid="save-button"]');
      assert.equal(saveButton.text(), 'Save');
    });

    it('allows editing content selection', () => {
      const wrapper = renderFilePicker();

      // Initially the content selector form is not visible.
      assert.isFalse(wrapper.exists('ContentSelector'));

      // Clicking on the change/edit button next to the content description
      // should show the content selector.
      clickEditButton(wrapper);
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

    it('cancels editing content when clicking "Cancel" button', () => {
      const wrapper = renderFilePicker();
      clickEditButton(wrapper);
      clickCancelEditButton(wrapper);
      assert.isFalse(wrapper.exists('ContentSelector'));
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    })
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
      })
    );
    assert.deepEqual(updatedConfig, {
      ...config,
      assignment,
      filePicker,
    });
  });
});
