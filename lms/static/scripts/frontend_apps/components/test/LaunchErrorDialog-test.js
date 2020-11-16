import { mount } from 'enzyme';
import { createElement } from 'preact';
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
      errorState: 'error-fetching-canvas-file',
      expectedText: "Hypothesis couldn't get the assignment's file from Canvas",
    },
    {
      errorState: 'canvas-file-not-found-in-course',
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
        assert.equal(wrapper.exists('Button'), retryAction !== null);
        if (retryAction) {
          assert.equal(wrapper.find('Button').prop('label'), retryAction);
        }
        assert.equal(wrapper.exists('ErrorDisplay'), hasDetailedError);
      });
    }
  );

  it('initiates retry when "Try again" button is clicked', () => {
    const wrapper = renderDialog();

    act(() => {
      wrapper.find('Button').prop('onClick')();
    });

    assert.called(retryStub);
  });

  it('enables "Try again" button if `busy` is false', () => {
    const wrapper = renderDialog({ busy: false });
    assert.isFalse(wrapper.find('Button').prop('disabled'));
  });

  it('disables "Try again" button if `busy` is true', () => {
    const wrapper = renderDialog({ busy: true });
    assert.isTrue(wrapper.find('Button').prop('disabled'));
  });

  it('shows error details', () => {
    const error = new Error('Oh no');
    const wrapper = renderDialog({
      errorState: 'error-fetching-canvas-file',
      error,
    });
    assert.equal(wrapper.find('ErrorDisplay').prop('error'), error);
  });
});
