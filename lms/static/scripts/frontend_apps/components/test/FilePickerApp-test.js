/* eslint-disable new-cap */

import { act } from 'preact/test-utils';
import { mount } from 'enzyme';
import { waitFor, waitForElement } from '../../../test-util/wait';

import { Config } from '../../config';
import FilePickerApp, { $imports } from '../FilePickerApp';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

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
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
        blackboard: {
          groupsEnabled: false,
        },
        canvas: {
          groupsEnabled: false,
        },
        ltiLaunchUrl: 'https://lms.anno.co/lti_launch',
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
      ltiLaunchURL: fakeConfig.filePicker.ltiLaunchUrl,
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
      assert.isFalse(wrapper.exists('FullScreenSpinner'));

      selectContent(wrapper, 'https://example.com');

      assert.isTrue(wrapper.exists('FullScreenSpinner'));
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
          extra_params: { groupSet: null },
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
    ['blackboard', 'canvas'].forEach(lmsWithGroups => {
      beforeEach(() => {
        fakeConfig.filePicker[lmsWithGroups].groupsEnabled = true;
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
            wrapper
              .find('LabeledButton[children="Continue"]')
              .props()
              .onClick();
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
          wrapper.find('LabeledButton[children="Continue"]').props().onClick();
        });

        assert.isTrue(wrapper.exists('FullScreenSpinner'));
      });
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

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    })
  );
});
