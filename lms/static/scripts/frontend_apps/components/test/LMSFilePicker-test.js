import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import { ApiError } from '../../utils/api';

import LMSFilePicker, { $imports } from '../LMSFilePicker';
import ErrorDisplay from '../ErrorDisplay';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('LMSFilePicker', () => {
  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ buttons, children }) => (
    <Fragment>
      {buttons} {children}
    </Fragment>
  );

  let FakeAuthWindow;
  let fakeApiCall;
  let fakeListFilesApi;
  let fakeAuthWindowInstance;

  const renderFilePicker = (props = {}) => {
    return mount(
      <LMSFilePicker
        authToken="auth-token"
        listFilesApi={fakeListFilesApi}
        onAuthorized={sinon.stub()}
        onSelectFile={sinon.stub()}
        onCancel={sinon.stub()}
        {...props}
      />
    );
  };

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves(['one file']);
    fakeAuthWindowInstance = {
      authorize: sinon.stub().resolves(null),
      close: () => {},
    };
    FakeAuthWindow = sinon.stub().returns(fakeAuthWindowInstance);

    fakeListFilesApi = {
      path: 'https://lms.anno.co/files/course123',
      authUrl: 'https://lms.anno.co/authorize-lms',
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/AuthWindow': FakeAuthWindow,
      '../utils/api': {
        apiCall: fakeApiCall,
      },
      './Dialog': FakeDialog,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('fetches files when the dialog first appears', async () => {
    const wrapper = renderFilePicker();
    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeListFilesApi.path,
    });
    const expectedFiles = await fakeApiCall.returnValues[0];
    wrapper.update();
    const fileList = wrapper.find('FileList');
    assert.deepEqual(fileList.prop('files'), expectedFiles);
  });

  it('shows the authorization prompt if fetching files fails with an ApiError that has no `errorMessage`', async () => {
    fakeApiCall.rejects(
      new ApiError('Not authorized', {
        /** without errorMessage */
      })
    );

    // Wait for the initial file fetch to fail.
    const wrapper = renderFilePicker();
    try {
      await fakeApiCall;
    } catch {
      /* unused */
    }
    wrapper.update();
    assert.called(fakeApiCall);

    // Check that the "Authorize" button is shown.
    const authButton = wrapper.find('LabeledButton[data-testid="authorize"]');
    assert.isTrue(authButton.exists());

    // Click the "Authorize" button and check that files are re-fetched.
    const authWindowClosed = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });
    const expectedFiles = [];
    fakeApiCall.reset();
    fakeApiCall.resolves(expectedFiles);

    authButton.prop('onClick')();
    // Wait for auth to complete, signaled by the window being closed.
    await authWindowClosed;
    wrapper.update();

    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeListFilesApi.path,
    });
    wrapper.update();
    const fileList = wrapper.find('FileList');
    assert.equal(fileList.prop('files'), expectedFiles);
  });

  it('shows the "Authorize" and "Try again" buttons after 2 failed authorization requests', async () => {
    fakeApiCall.rejects(
      new ApiError('Not authorized', {
        /** without errorMessage */
      })
    );

    const wrapper = renderFilePicker();
    try {
      await fakeApiCall;
    } catch {
      /* unused */
    }
    wrapper.update();
    assert.called(fakeApiCall);

    // After first failed authentication request
    const authorizeButton = wrapper.find(
      'LabeledButton[data-testid="authorize"]'
    );
    assert.isTrue(authorizeButton.exists());
    assert.isTrue(wrapper.exists('p[data-testid="authorization warning"]'));

    // Make unsuccessful authorization attempt and wait for the auth window to close.
    const authWindowClosed = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });
    authorizeButton.prop('onClick')();
    await authWindowClosed;
    wrapper.update();

    // After second failed authentication request
    const authorizeAgainButton = wrapper.find(
      'LabeledButton[data-testid="try-again"]'
    );
    assert.isTrue(authorizeAgainButton.exists());
    assert.equal(authorizeAgainButton.text(), 'Try again');
    const errorDetails = wrapper.find('ErrorDisplay');
    assert.equal(
      errorDetails.prop('message'),
      'Failed to authorize file access'
    );
    assert.equal(errorDetails.prop('error').message, '');

    // Make successful authorization attempt and wait for the auth window to close.
    fakeApiCall.reset();
    fakeApiCall.resolves([0]);
    await fakeApiCall;
    wrapper.update();

    const authWindowClosed2 = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });
    wrapper.find('LabeledButton[data-testid="try-again"]').prop('onClick')();
    await authWindowClosed2;
    wrapper.update();

    // After authorization completes, files should be fetched and then the
    // file list should be displayed.
    assert.isTrue(wrapper.exists('FileList'), 'File list was not displayed');
    assert.isFalse(wrapper.exists('LabeledButton[data-testid="authorize"]'));
    assert.isFalse(wrapper.exists('p[data-testid="authorization warning"]'));
    assert.isFalse(wrapper.exists('LabeledButton[data-testid="try-again"]'));
    assert.isFalse(wrapper.exists('ErrorDisplay'));
  });

  [
    {
      description: 'a server error with details',
      error: new ApiError('Not authorized', {
        message: 'Some error detail',
      }),
    },
    {
      description: 'a network or other error',
      error: new Error('Failed to fetch'),
    },
  ].forEach(({ description, error }) => {
    it(`shows error details and "Try again" button if fetching files fails with ${description}`, async () => {
      fakeApiCall.rejects(error);

      const authWindowClosed = new Promise(resolve => {
        fakeAuthWindowInstance.close = resolve;
      });

      // When the dialog is initially displayed, it should try to fetch files.
      const wrapper = renderFilePicker();
      try {
        await fakeApiCall;
      } catch {
        /* unused */
      }
      wrapper.update();
      assert.called(fakeApiCall);

      // The details of the error should be displayed, along with a "Try again"
      // button.
      const tryAgainButton = wrapper.find(
        'LabeledButton[data-testid="try-again"]'
      );
      assert.isTrue(tryAgainButton.exists());

      const errorDetails = wrapper.find(ErrorDisplay);
      assert.include(errorDetails.props(), {
        message: 'There was a problem fetching files',
        error,
      });

      // Clicking the "Try again" button should re-try authorization.
      fakeApiCall.reset();
      fakeApiCall.resolves([]);

      tryAgainButton.prop('onClick')();
      await authWindowClosed;
      wrapper.update();

      // After authorization completes, files should be fetched and then the
      // file list should be displayed.
      await fakeApiCall;
      wrapper.update();
      assert.isTrue(wrapper.exists('FileList'), 'File list was not displayed');
    });
  });

  it('shows "Reload" button when the request returns no files', async () => {
    const clock = sinon.useFakeTimers();
    fakeApiCall.onFirstCall().resolves([]);
    // When the dialog is initially displayed, it should try to fetch files.
    const wrapper = renderFilePicker();
    await fakeApiCall;
    wrapper.update();
    assert.called(fakeApiCall);

    const reloadButton = wrapper.find('LabeledButton[data-testid="reload"]');
    assert.isFalse(reloadButton.prop('disabled'));

    const waitMs = 3000;
    fakeApiCall
      .onSecondCall()
      .resolves(new Promise(resolve => setTimeout(() => resolve([]), waitMs)));

    reloadButton.prop('onClick')();
    wrapper.update();

    assert.isTrue(
      wrapper.find('LabeledButton[data-testid="reload"]').prop('disabled')
    );

    clock.tick(waitMs);
    await fakeApiCall;
    wrapper.update();

    assert.isFalse(
      wrapper.find('LabeledButton[data-testid="reload"]').prop('disabled')
    );

    clock.restore();
  });

  it('shows a "Select" button when the request return a list with one or more files', async () => {
    fakeApiCall.resolves([0]);
    // When the dialog is initially displayed, it should try to fetch files.
    const wrapper = renderFilePicker();
    await fakeApiCall;
    wrapper.update();
    assert.called(fakeApiCall);

    assert.isTrue(wrapper.exists('LabeledButton[data-testid="select"]'));
  });

  it('closes the authorization window if open when canceling the dialog', async () => {
    // Make the initial file list request fail, to trigger a prompt to authorize.
    fakeApiCall.rejects(
      new ApiError('Not authorized', {
        /** without errorMessage */
      })
    );

    // Click the "Authorize" button to show the authorization popup.
    const wrapper = renderFilePicker();
    try {
      await fakeApiCall;
    } catch {
      /* unused  */
    }
    wrapper.update();

    const closePopup = sinon.stub();
    FakeAuthWindow.returns({
      authorize: sinon.stub().resolves(null),
      close: closePopup,
    });
    wrapper.find('LabeledButton[data-testid="authorize"]').prop('onClick')();

    // Dismiss the LMS file picker. This should close the auth popup.
    wrapper.find(FakeDialog).prop('onCancel')();

    assert.called(closePopup);
  });

  it('does not show an authorization window when mounted', () => {
    const wrapper = renderFilePicker();
    assert.notCalled(FakeAuthWindow);
    assert.isFalse(wrapper.exists('Button[label="Authorize"]'));
  });

  it('fetches and displays files from the LMS', async () => {
    const wrapper = renderFilePicker();
    const expectedFiles = await fakeApiCall.returnValues[0];
    wrapper.update();
    assert.called(fakeApiCall);

    const fileList = wrapper.find('FileList');
    assert.deepEqual(fileList.prop('files'), expectedFiles);
  });

  it('maintains selected file state', async () => {
    const wrapper = renderFilePicker();
    await fakeApiCall;
    wrapper.update();

    const file = { id: 123 };

    wrapper.find('FileList').prop('onSelectFile')(file);
    wrapper.update();

    assert.equal(wrapper.find('FileList').prop('selectedFile'), file);
  });

  it('invokes `onSelectFile` when user chooses a file', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile });
    await fakeApiCall;
    wrapper.update();

    const file = { id: 123 };
    wrapper.find('FileList').prop('onUseFile')(file);
    assert.calledWith(onSelectFile, file);
  });

  it('disables "Select" button when no file is selected', async () => {
    const wrapper = renderFilePicker();
    await fakeApiCall;
    wrapper.update();

    assert.equal(
      wrapper.find('LabeledButton[data-testid="select"]').prop('disabled'),
      true
    );
  });

  it('enables "Select" button when a file is selected', async () => {
    const wrapper = renderFilePicker();
    await fakeApiCall;
    wrapper.update();

    wrapper.find('FileList').prop('onSelectFile')({ id: 123 });
    wrapper.update();

    assert.equal(
      wrapper.find('LabeledButton[data-testid="select"]').prop('disabled'),
      false
    );
  });

  it('chooses selected file when uses clicks "Select" button', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile });
    await fakeApiCall;
    wrapper.update();

    const file = { id: 123 };

    wrapper.find('FileList').prop('onSelectFile')(file);
    wrapper.update();

    wrapper.find('LabeledButton[data-testid="select"]').prop('onClick')();

    assert.calledWith(onSelectFile, file);
  });

  it('does not render anything while fetching', async () => {
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.isEmptyRender());

    await fakeApiCall;
    wrapper.update();
    assert.isFalse(wrapper.isEmptyRender());
  });
});
