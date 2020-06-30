import { Fragment, createElement } from 'preact';
import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

import { ApiError } from '../../utils/api';

import LMSFilePicker, { $imports } from '../LMSFilePicker';
import ErrorDisplay from '../ErrorDisplay';

describe('LMSFilePicker', () => {
  const FakeButton = () => null;
  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ buttons, children }) => (
    <Fragment>
      {buttons} {children}
    </Fragment>
  );
  const FakeFileList = () => null;

  let FakeAuthWindow;
  let fakeListFiles;
  let fakeAuthWindowInstance;

  const renderFilePicker = (props = {}) => {
    return mount(
      <LMSFilePicker
        authToken="auth-token"
        authUrl="https://lms.anno.co/authorize-lms"
        courseId="test-course"
        onAuthorized={sinon.stub()}
        onSelectFile={sinon.stub()}
        onCancel={sinon.stub()}
        {...props}
      />
    );
  };

  beforeEach(() => {
    fakeAuthWindowInstance = {
      authorize: sinon.stub().resolves(null),
      close: () => {},
    };
    FakeAuthWindow = sinon.stub().returns(fakeAuthWindowInstance);

    fakeListFiles = sinon.stub().resolves([]);

    $imports.$mock({
      '../utils/AuthWindow': FakeAuthWindow,
      '../utils/api': {
        listFiles: fakeListFiles,
      },
      './Button': FakeButton,
      './Dialog': FakeDialog,
      './FileList': FakeFileList,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('fetches files when the dialog first appears', async () => {
    const wrapper = renderFilePicker();
    assert.called(fakeListFiles);
    const expectedFiles = await fakeListFiles.returnValues[0];
    wrapper.update();
    const fileList = wrapper.find(FakeFileList);
    assert.deepEqual(fileList.prop('files'), expectedFiles);
  });

  it('shows the authorization prompt if fetching files fails with an ApiError that has no `errorMessage`', async () => {
    fakeListFiles.rejects(new ApiError('Not authorized', {}));

    const wrapper = renderFilePicker();
    assert.called(fakeListFiles);

    try {
      await fakeListFiles.returnValues[0];
    } catch (err) {
      /* unused */
    }

    wrapper.update();
    assert.isTrue(wrapper.exists('FakeButton[label="Authorize"]'));
  });

  it('shows the try again prompt after a failed authorization attempt', async () => {
    fakeListFiles.rejects(new ApiError('Not authorized', {}));

    const authWindowClosed = new Promise(resolve => {
      fakeAuthWindowInstance.close = resolve;
    });

    const wrapper = renderFilePicker();
    assert.called(fakeListFiles);

    try {
      await fakeListFiles.returnValues[0];
    } catch (err) {
      /* unused */
    }

    wrapper.update();

    // Make an authorization attempt and wait for the auth window to close.
    await act(async () => {
      wrapper.find('FakeButton[label="Authorize"]').props().onClick();
      await authWindowClosed;
    });

    wrapper.update();

    assert.isTrue(wrapper.exists('FakeButton[label="Try again"]'));

    const errorDetails = wrapper.find(ErrorDisplay);
    assert.isTrue(
      errorDetails.text().includes('Failed to authorize with Canvas')
    );
    assert.equal(errorDetails.props().error.message, '');
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
      fakeListFiles.rejects(error);

      // When the dialog is initially displayed, it should try to fetch files.
      const wrapper = renderFilePicker();
      assert.called(fakeListFiles);

      try {
        await fakeListFiles.returnValues[0];
      } catch (err) {
        /* unused */
      }
      wrapper.update();

      // The details of the error should be displayed, along with a "Try again"
      // button.
      const tryAgainButton = wrapper.find('FakeButton[label="Try again"]');
      assert.isTrue(tryAgainButton.exists());

      const errorDetails = wrapper.find(ErrorDisplay);
      assert.include(errorDetails.props(), {
        message: 'There was a problem fetching files',
        error,
      });

      // Clicking the "Try again" button should re-try authorization.
      fakeListFiles.reset();
      fakeListFiles.resolves([]);
      tryAgainButton.prop('onClick')();
      assert.called(FakeAuthWindow);

      // After authorization completes, files should be fetched and then the
      // file list should be displayed.
      await fakeListFiles.returnValues[0];
      wrapper.update();
      assert.isTrue(
        wrapper.exists('FakeFileList'),
        'File list was not displayed'
      );
    });
  });

  it('closes the authorization window if open when canceling the dialog', async () => {
    // Make the initial file list request fail, to trigger a prompt to authorize.
    fakeListFiles.rejects(new ApiError('Not authorized', {}));

    const closePopup = sinon.stub();
    FakeAuthWindow.returns({
      authorize: sinon.stub().resolves(null),
      close: closePopup,
    });

    // Click the "Authorize" button to show the authorization popup.
    const wrapper = renderFilePicker();
    try {
      await fakeListFiles.returnValues[0];
    } catch (e) {
      // Ignored
    }
    wrapper.update();
    wrapper.find('FakeButton[label="Authorize"]').prop('onClick')();

    // Dismiss the LMS file picker. This should close the auth popup.
    wrapper.find(FakeDialog).props().onCancel();

    assert.called(closePopup);
  });

  it('does not show an authorization window when mounted', () => {
    const wrapper = renderFilePicker();
    assert.notCalled(FakeAuthWindow);
    assert.isFalse(wrapper.exists('FakeButton[label="Authorize"]'));
  });

  it('fetches and displays files from the LMS', async () => {
    const wrapper = renderFilePicker();
    assert.called(fakeListFiles);

    const expectedFiles = await fakeListFiles.returnValues[0];
    wrapper.update();

    const fileList = wrapper.find(FakeFileList);
    assert.deepEqual(fileList.prop('files'), expectedFiles);
  });

  it('shows a loading indicator while fetching files', async () => {
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.find(FakeFileList).prop('isLoading'));

    await fakeListFiles.returnValues[0];
    wrapper.update();

    assert.isFalse(wrapper.find(FakeFileList).prop('isLoading'));
  });

  it('maintains selected file state', () => {
    const wrapper = renderFilePicker();
    const file = { id: 123 };

    act(() => {
      wrapper.find(FakeFileList).props().onSelectFile(file);
    });
    wrapper.update();

    assert.equal(wrapper.find(FakeFileList).prop('selectedFile'), file);
  });

  it('invokes `onSelectFile` when user chooses a file', () => {
    const onSelectFile = sinon.stub();
    const file = { id: 123 };
    const wrapper = renderFilePicker({ onSelectFile });
    wrapper.find(FakeFileList).props().onUseFile(file);
    assert.calledWith(onSelectFile, file);
  });

  it('shows disabled "Select" button when no file is selected', () => {
    const wrapper = renderFilePicker();
    assert.equal(
      wrapper.find('FakeButton[label="Select"]').prop('disabled'),
      true
    );
  });

  it('shows enabled "Select" button when a file is selected', () => {
    const wrapper = renderFilePicker();
    act(() => {
      wrapper.find(FakeFileList).props().onSelectFile({ id: 123 });
    });
    wrapper.update();
    assert.equal(
      wrapper.find('FakeButton[label="Select"]').prop('disabled'),
      false
    );
  });

  it('chooses selected file when uses clicks "Select" button', () => {
    const onSelectFile = sinon.stub();
    const file = { id: 123 };
    const wrapper = renderFilePicker({ onSelectFile });

    act(() => {
      wrapper.find(FakeFileList).props().onSelectFile(file);
    });
    wrapper.update();

    act(() => {
      wrapper.find('FakeButton[label="Select"]').props().onClick();
    });

    assert.calledWith(onSelectFile, file);
  });
});
