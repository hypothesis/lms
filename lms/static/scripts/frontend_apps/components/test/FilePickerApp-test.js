/* eslint-disable new-cap */

import { createElement } from 'preact';
import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

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
  function checkFormFields(wrapper, expectedContent, expectedGroupSet) {
    const formFields = wrapper.find('FilePickerFormFields');
    assert.deepEqual(formFields.props(), {
      children: [],
      content: expectedContent,
      formFields: fakeConfig.filePicker.formFields,
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

  function selectContent(wrapper, url) {
    const picker = wrapper.find('ContentSelector');
    interact(wrapper, () => {
      picker.props().onSelectContent({
        type: 'url',
        url,
      });
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
          useGroupSet ? 'groupSet1' : null
        );
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
