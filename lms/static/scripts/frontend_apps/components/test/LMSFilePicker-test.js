import { Fragment, createElement } from 'preact';
import { act } from 'preact/test-utils';
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
    fakeApiCall = sinon.stub().resolves([]);
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
    assert.called(fakeApiCall);

    try {
      await fakeApiCall.returnValues[0];
    } catch (err) {
      /* unused */
    }
    wrapper.update();

    // Check that the "Authorize" button is shown.
    const authWindowClosed = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });
    const authButton = wrapper.find('Button[label="Authorize"]');
    assert.isTrue(authButton.exists());

    // Click the "Authorize" button and check that files are re-fetched.
    const expectedFiles = [];
    fakeApiCall.reset();
    fakeApiCall.resolves(expectedFiles);
    await act(async () => {
      authButton.props().onClick();
      // Wait for auth to complete, signaled by the window being closed.
      await authWindowClosed;
    });
    wrapper.update();

    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeListFilesApi.path,
    });
    wrapper.update();
    const fileList = wrapper.find('FileList');
    assert.equal(fileList.prop('files'), expectedFiles);
  });

  it('shows the "Authorize" and "Authorize again" buttons after 2 failed authorization requests', async () => {
    fakeApiCall.rejects(
      new ApiError('Not authorized', {
        /** without errorMessage */
      })
    );

    const authWindowClosed = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });

    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    try {
      await fakeApiCall.returnValues[0];
    } catch (err) {
      /* unused */
    }
    wrapper.update();

    // After first failed authentication request
    const authorizeButton = wrapper.find('Button[label="Authorize"]');
    assert.isTrue(authorizeButton.exists());
    assert.isTrue(wrapper.exists('p[data-testid="authorization warning"]'));

    // Make first (unsuccesful) authorization attempt and wait for the auth window to close.
    await act(async () => {
      authorizeButton.props().onClick();
      await authWindowClosed;
    });
    wrapper.update();

    // After second failed authentication request
    const authorizeAgainButton = wrapper.find(
      'Button[label="Authorize again"]'
    );
    assert.isTrue(authorizeAgainButton.exists());
    const errorDetails = wrapper.find('ErrorDisplay');
    assert.equal(
      errorDetails.prop('message'),
      'Failed to authorize file access'
    );
    assert.equal(errorDetails.prop('error').message, '');

    // Make second (successful) authorization attempt and wait for the auth window to close.
    fakeApiCall.reset();
    fakeApiCall.resolves([]);
    await fakeApiCall.returnValues[0];
    await act(async () => {
      authorizeAgainButton.props().onClick();
      await authWindowClosed;
    });
    wrapper.update();

    // After authorization completes, files should be fetched and then the
    // file list should be displayed.
    assert.isTrue(wrapper.exists('FileList'), 'File list was not displayed');
    assert.isFalse(wrapper.exists('Button[label="Authorize"]'));
    assert.isFalse(wrapper.exists('p[data-testid="authorization warning"]'));
    assert.isFalse(wrapper.exists('Button[label="Authorize again"]'));
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
      assert.called(fakeApiCall);

      try {
        await fakeApiCall.returnValues[0];
      } catch (err) {
        /* unused */
      }
      wrapper.update();

      // The details of the error should be displayed, along with a "Try again"
      // button.
      const tryAgainButton = wrapper.find('Button[label="Try again"]');
      assert.isTrue(tryAgainButton.exists());

      const errorDetails = wrapper.find(ErrorDisplay);
      assert.include(errorDetails.props(), {
        message: 'There was a problem fetching files',
        error,
      });

      // Clicking the "Try again" button should re-try authorization.
      fakeApiCall.reset();
      fakeApiCall.resolves([]);
      await act(async () => {
        tryAgainButton.props().onClick();
        await authWindowClosed;
      });
      wrapper.update();

      // After authorization completes, files should be fetched and then the
      // file list should be displayed.
      await fakeApiCall.returnValues[0];
      wrapper.update();
      assert.isTrue(wrapper.exists('FileList'), 'File list was not displayed');
    });
  });

  it('shows "Reload" button when the request returns an empty list of files', async () => {
    fakeApiCall.resolves([]);
    // When the dialog is initially displayed, it should try to fetch files.
    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    try {
      await fakeApiCall.returnValues[0];
    } catch (err) {
      /* unused */
    }
    wrapper.update();

    assert.isTrue(wrapper.exists('Button[label="Reload"]'));
  });

  it('shows a "Select" button when the request return a list with one or more files', async () => {
    fakeApiCall.resolves([0]);
    // When the dialog is initially displayed, it should try to fetch files.
    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    try {
      await fakeApiCall.returnValues[0];
    } catch (err) {
      /* unused */
    }
    wrapper.update();

    assert.isTrue(wrapper.exists('Button[label="Select"]'));
  });

  it('closes the authorization window if open when canceling the dialog', async () => {
    // Make the initial file list request fail, to trigger a prompt to authorize.
    fakeApiCall.rejects(
      new ApiError('Not authorized', {
        /** without errorMessage */
      })
    );

    const closePopup = sinon.stub();
    FakeAuthWindow.returns({
      authorize: sinon.stub().resolves(null),
      close: closePopup,
    });

    // Click the "Authorize" button to show the authorization popup.
    const wrapper = renderFilePicker();
    try {
      await fakeApiCall.returnValues[0];
    } catch (e) {
      // Ignored
    }
    wrapper.update();
    wrapper.find('Button[label="Authorize"]').prop('onClick')();

    // Dismiss the LMS file picker. This should close the auth popup.
    wrapper.find(FakeDialog).props().onCancel();

    assert.called(closePopup);
  });

  it('does not show an authorization window when mounted', () => {
    const wrapper = renderFilePicker();
    assert.notCalled(FakeAuthWindow);
    assert.isFalse(wrapper.exists('Button[label="Authorize"]'));
  });

  it('fetches and displays files from the LMS', async () => {
    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    const expectedFiles = await fakeApiCall.returnValues[0];
    wrapper.update();

    const fileList = wrapper.find('FileList');
    assert.deepEqual(fileList.prop('files'), expectedFiles);
  });

  it('shows a loading indicator while fetching files', async () => {
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.find('FileList').prop('isLoading'));

    await fakeApiCall.returnValues[0];
    wrapper.update();

    assert.isFalse(wrapper.find('FileList').prop('isLoading'));
  });

  it('maintains selected file state', () => {
    const wrapper = renderFilePicker();
    const file = { id: 123 };

    act(() => {
      wrapper.find('FileList').props().onSelectFile(file);
    });
    wrapper.update();

    assert.equal(wrapper.find('FileList').prop('selectedFile'), file);
  });

  it('invokes `onSelectFile` when user chooses a file', () => {
    const onSelectFile = sinon.stub();
    const file = { id: 123 };
    const wrapper = renderFilePicker({ onSelectFile });
    wrapper.find('FileList').props().onUseFile(file);
    assert.calledWith(onSelectFile, file);
  });

  it('shows disabled "Select" button when no file is selected', () => {
    const wrapper = renderFilePicker();
    assert.equal(wrapper.find('Button[label="Select"]').prop('disabled'), true);
  });

  it('shows enabled "Select" button when a file is selected', () => {
    const wrapper = renderFilePicker();
    act(() => {
      wrapper.find('FileList').props().onSelectFile({ id: 123 });
    });
    wrapper.update();
    assert.equal(
      wrapper.find('Button[label="Select"]').prop('disabled'),
      false
    );
  });

  it('chooses selected file when uses clicks "Select" button', () => {
    const onSelectFile = sinon.stub();
    const file = { id: 123 };
    const wrapper = renderFilePicker({ onSelectFile });

    act(() => {
      wrapper.find('FileList').props().onSelectFile(file);
    });
    wrapper.update();

    act(() => {
      wrapper.find('Button[label="Select"]').props().onClick();
    });

    assert.calledWith(onSelectFile, file);
  });
});
