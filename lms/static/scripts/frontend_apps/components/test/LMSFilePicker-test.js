import {
  mockImportedComponents,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { APIError } from '../../errors';
import DocumentList from '../DocumentList';
import LMSFilePicker, { $imports } from '../LMSFilePicker';

describe('LMSFilePicker', () => {
  let fakeApiCall;
  let fakeListFilesApi;
  let fakeFiles;
  let fakeFolders;

  const renderFilePicker = (props = {}) => {
    return mount(
      <LMSFilePicker
        authToken="auth-token"
        listFilesApi={fakeListFilesApi}
        onAuthorized={sinon.stub()}
        onSelectFile={sinon.stub()}
        onCancel={sinon.stub()}
        missingFilesHelpLink={'https://fake_help_link'}
        {...props}
      />,
    );
  };

  const changePath = (wrapper, folder) => {
    act(() => wrapper.find('Breadcrumbs').props().onSelectItem(folder));
  };

  beforeEach(() => {
    fakeFiles = [
      { type: 'File', display_name: 'A file' },
      { type: 'Folder', display_name: 'A folder' },
    ];

    fakeFolders = [
      {
        display_name: 'Subfolder',
        id: 'subfolder',
        type: 'Folder',
        contents: {
          path: 'folder-path',
        },
      },
      {
        display_name: 'Subfolder2',
        id: 'subfolder2',
        type: 'Folder',
        contents: {
          path: 'folder2-path',
        },
      },
    ];

    fakeListFilesApi = {
      path: 'https://lms.anno.co/files/course123',
      authUrl: 'https://lms.anno.co/authorize-lms',
    };

    fakeApiCall = sinon.stub().resolves(fakeFiles);

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/api': {
        apiCall: fakeApiCall,
      },
      // Don't mock <DocumentList> because <NoFiles> requires
      // it to render for code coverage.
      './DocumentList': DocumentList,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('fetches files when the component is first rendered', async () => {
    const wrapper = renderFilePicker();

    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeListFilesApi.path,
    });

    const expectedFiles = await fakeApiCall.returnValues[0];
    const fileList = await waitForElement(wrapper, 'DocumentList');
    assert.deepEqual(fileList.prop('documents'), expectedFiles);
  });

  it('shows a full-screen spinner when the component is fetching', async () => {
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.find('SpinnerOverlay').exists());

    await waitForElement(wrapper, 'DocumentList');
    assert.isFalse(wrapper.find('SpinnerOverlay').exists());
  });

  it('shows breadcrumbs if `withBreadcrumbs` enabled', async () => {
    const wrapper = renderFilePicker({ withBreadcrumbs: true });

    const breadcrumbs = await waitForElement(wrapper, 'Breadcrumbs');

    const items = breadcrumbs.props().items;
    assert.lengthOf(items, 1);
    assert.include(
      items[0],
      {
        display_name: 'Files',
        id: '__root__',
      },
      'The only initial breadcrumb is the top-level "Files" crumb',
    );

    assert.equal(
      breadcrumbs.props().renderItem(fakeFolders[0]),
      'Subfolder',
      'The `renderItem` callback passed to Breadcrumbs renders a File `display_name`',
    );
  });

  it('fetches files in indicated sub-folder if folder path is changed', async () => {
    const wrapper = renderFilePicker({ withBreadcrumbs: true });

    const breadcrumbs = await waitForElement(wrapper, 'Breadcrumbs');
    fakeApiCall.resetHistory();

    // Simulate changing the folder path, as if a user clicked on a "crumb"
    act(() => breadcrumbs.props().onSelectItem(fakeFolders[0]));

    await waitFor(() => fakeApiCall.calledOnce);

    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeFolders[0].contents.path,
    });
  });

  it('does not fetch files for a folder if files were previously loaded', async () => {
    const folderWithChildren = {
      type: 'Folder',
      display_name: 'A folder with children',
      children: fakeFiles,
    };

    const wrapper = renderFilePicker({ withBreadcrumbs: true });
    const breadcrumbs = await waitForElement(wrapper, 'Breadcrumbs');
    fakeApiCall.resetHistory();

    // Simulate changing the folder path, as if a user clicked on a "crumb"
    act(() => breadcrumbs.props().onSelectItem(folderWithChildren));

    assert.notCalled(fakeApiCall);
  });

  it('updates Breadcrumbs when folder path changes', async () => {
    const wrapper = renderFilePicker({ withBreadcrumbs: true });
    await waitForElement(wrapper, 'Breadcrumbs');

    // Simulate changing the path into subfolder `fakeFolders[0]`
    changePath(wrapper, fakeFolders[0]);
    wrapper.update();

    const breadcrumbs = wrapper.find('Breadcrumbs');
    const pathItems = breadcrumbs.props().items;

    // Now there is the top "Files" item and a single subfolder
    assert.lengthOf(pathItems, 2);
    // The last item is the sub-folder just changed to, `fakeFolders[0]`
    assert.deepEqual(pathItems[1], fakeFolders[0]);

    // Simulate changing the path again into a nested subfolder `fakeFolders[1]`
    changePath(wrapper, fakeFolders[1]);
    wrapper.update();
    const pathItems2 = wrapper.find('Breadcrumbs').props().items;

    // Now there are three breadcrumbs, with `fakeFolders[1]` as the last item
    assert.lengthOf(pathItems2, 3);
    assert.deepEqual(pathItems2[2], fakeFolders[1]);

    // Now head back "up" the hierarchy one level (`fakeFolders[0]`)
    changePath(wrapper, fakeFolders[0]);
    wrapper.update();
    const pathItems3 = wrapper.find('Breadcrumbs').props().items;

    // This removes `fakeFolders[1]` from the path items, and the last item is
    // the folder path just switched to (`fakeFolders[0]`)
    assert.lengthOf(pathItems3, 2);
    assert.deepEqual(pathItems3[1], fakeFolders[0]);
  });

  it('shows the authorization prompt if fetching files fails with an APIError that has no `serverMessage`', async () => {
    fakeApiCall.rejects(
      new APIError('Not authorized', {
        /** without serverMessage */
      }),
    );

    // Wait for the initial file fetch to fail.
    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    // Check that the "Authorize" button is shown.
    const authButton = await waitForElement(wrapper, 'AuthButton');
    assert.isTrue(authButton.exists());

    // Click the "Authorize" button and check that files are re-fetched.
    const expectedFiles = ['a file'];
    fakeApiCall.reset();
    fakeApiCall.resolves(expectedFiles);

    await act(() => authButton.prop('onAuthComplete')());
    wrapper.update();

    assert.calledWith(fakeApiCall, {
      authToken: 'auth-token',
      path: fakeListFilesApi.path,
    });

    const fileList = wrapper.find('DocumentList');
    assert.deepEqual(fileList.prop('documents'), expectedFiles);
  });

  it('shows the "Authorize" and "Try again" buttons after 2 failed authorization requests', async () => {
    fakeApiCall.rejects(
      new APIError('Not authorized', {
        /** without serverMessage */
      }),
    );

    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    // Make initial authorization request, which fails.
    const authButton = await waitForElement(wrapper, 'AuthButton');
    assert.isTrue(authButton.exists());
    assert.isTrue(wrapper.exists('p[data-testid="authorization warning"]'));

    // Make unsuccessful authorization attempt and wait for re-fetching files
    // to fail.
    await act(() => authButton.prop('onAuthComplete')());
    wrapper.update();

    // Make second authorization request, which succeeds.
    const tryAgainButton = wrapper.find('AuthButton');
    assert.isTrue(tryAgainButton.exists());
    assert.equal(tryAgainButton.prop('label'), 'Try again');
    const errorDetails = wrapper.find('[data-testid="authorization warning"]');
    assert.equal(errorDetails.text(), 'Unable to authorize file access.');

    // Make successful authorization attempt and wait for the auth window to close.
    fakeApiCall.reset();
    fakeApiCall.resolves([0]);

    await act(() => tryAgainButton.prop('onAuthComplete')());
    wrapper.update();

    // After authorization completes, files should be fetched and then the
    // file list should be displayed.
    assert.isTrue(wrapper.exists('DocumentList'));
    assert.isFalse(wrapper.exists('AuthButton'));
    assert.isFalse(wrapper.exists('p[data-testid="authorization warning"]'));
    assert.isFalse(wrapper.exists('ErrorDisplay'));
  });

  [
    {
      description: 'a server error with details',
      error: new APIError('Not authorized', {
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

      // When the dialog is initially displayed, it should try to fetch files.
      const wrapper = renderFilePicker();
      assert.called(fakeApiCall);

      // The details of the error should be displayed, along with a "Try again"
      // button.
      const tryAgainButton = await waitForElement(wrapper, 'AuthButton');
      assert.isTrue(tryAgainButton.exists());

      const errorDetails = wrapper.find('ErrorDisplay');
      assert.include(errorDetails.props(), {
        description: 'There was a problem fetching files',
        error,
      });

      // Clicking the "Try again" button should re-try authorization.
      fakeApiCall.reset();
      fakeApiCall.resolves([]);

      await act(() => tryAgainButton.prop('onAuthComplete')());
      wrapper.update();

      // After authorization completes, files should be fetched and then the
      // file list should be displayed.
      assert.isTrue(
        wrapper.exists('DocumentList'),
        'File list was not displayed',
      );
    });
  });

  it('shows "Reload" button when the request returns no files', async () => {
    fakeApiCall.onFirstCall().resolves([]);

    // After first render, the component will kick off the first file API fetch
    const wrapper = renderFilePicker();
    const reloadButton = await waitForElement(
      wrapper,
      'button[data-testid="reload"]',
    );
    assert.equal(reloadButton.text(), 'Reload');
    assert.isNotOk(reloadButton.prop('disabled'));

    // Simulate a user clicking the Reload button and dispatching another
    // API request. Leave the next fetch (Promise) unsettled (as if
    // loading is ongoing).
    let outsideResolve;
    fakeApiCall.onSecondCall().resolves(
      new Promise(resolve => {
        outsideResolve = resolve;
      }),
    );
    // Click the button to kick off the next request, which will hang...
    act(() => {
      reloadButton.prop('onClick')();
    });
    wrapper.update();

    // Request Promise is still unsettled, so the component stays in a "fetching"
    // state [1]. It should still show the "Reload" label on the continue button,
    // but the button should be disabled.
    //
    // [1]: Because it's `fetching` and not `fetched`, the button's testid
    // is "select" instead of "reload"
    await waitForElement(wrapper, 'button[data-testid="select"]');
    const waitingReloadButton = wrapper.find('button[data-testid="select"]');
    assert.isTrue(waitingReloadButton.prop('disabled'));
    assert.equal(waitingReloadButton.text(), 'Reload');

    // Now resolve that hanging API request Promise to an empty list (of files)
    outsideResolve([]);
    wrapper.update();

    // The component will move into a `fetched` state, and will once again
    // provide an enabled continue button to attempt a reload
    await waitForElement(wrapper, 'button[data-testid="reload"]');
    const finalReloadButton = wrapper.find('button[data-testid="reload"]');
    assert.equal(finalReloadButton.text(), 'Reload');
    assert.isNotOk(finalReloadButton.prop('disabled'));
  });

  it('loads the set of files for the active directory when user clicks "Reload"', async () => {
    fakeApiCall.resolves([]);

    const wrapper = renderFilePicker({ withBreadcrumbs: true });

    // Set the active directory to a sub-directory in folderPath
    await waitForElement(wrapper, 'Breadcrumbs');
    changePath(wrapper, fakeFolders[0]);

    // Make next call resolve to a full tree of files and folders.
    const expectedFiles = [fakeFiles[0]];
    fakeApiCall.resolves([
      {
        ...fakeFolders[0],
        children: expectedFiles,
      },
      fakeFolders[1],
    ]);

    // The file list is empty. The continue button should have a "Reload" label.
    const reloadButton = await waitForElement(
      wrapper,
      'button[data-testid="reload"]',
    );
    assert.equal(reloadButton.text(), 'Reload');

    await act(() => reloadButton.prop('onClick')());

    const fileList = await waitForElement(wrapper, 'DocumentList');

    // It should set the file list to the files for the active directory,
    // not the root directory
    assert.equal(fileList.props().documents, expectedFiles);
  });

  it('shows a "Select" button when the request return a list with one or more files', async () => {
    fakeApiCall.resolves([0]);
    // When the dialog is initially displayed, it should try to fetch files.
    const wrapper = renderFilePicker();
    assert.called(fakeApiCall);

    const continueButton = await waitForElement(
      wrapper,
      'button[data-testid="select"]',
    );
    assert.equal(continueButton.text(), 'Select');
    // No file is selected, so the button is disabled
    assert.isTrue(continueButton.prop('disabled'));
  });

  it('fetches and displays files from the LMS', async () => {
    const wrapper = renderFilePicker();
    const expectedFiles = await fakeApiCall.returnValues[0];
    wrapper.update();
    assert.called(fakeApiCall);

    const fileList = await waitForElement(wrapper, 'DocumentList');
    assert.deepEqual(fileList.prop('documents'), expectedFiles);
  });

  it('maintains selected file state', async () => {
    const wrapper = renderFilePicker();
    const file = { id: 123 };

    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onSelectDocument')(file);
    wrapper.update();

    assert.equal(wrapper.find('DocumentList').prop('selectedDocument'), file);
  });

  it('invokes `onSelectFile` when user chooses a file', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile });

    const file = { id: 123 };
    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onUseDocument')(file);
    assert.calledWith(onSelectFile, file);
  });

  it('does not invoke `onSelectFile` if chosen file is empty', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile });

    const file = null;
    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onUseDocument')(file);
    assert.notCalled(onSelectFile);
  });

  it('updates the folder path when a user chooses a folder', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile, withBreadcrumbs: true });

    const file = fakeFiles[1]; // This is a folder
    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onUseDocument')(file);
    // Folders cannot be selected as a file...
    assert.notCalled(onSelectFile);

    await waitFor(() => fakeApiCall.calledTwice, 50);
    wrapper.update();

    // ...Instead, the path state is updated (and "navigated to") and added
    // to the set of breadcrumb path elements
    assert.equal(wrapper.find('Breadcrumbs').props().items[1], fakeFiles[1]);
  });

  it('disables "Select" button when no file is selected', async () => {
    const wrapper = renderFilePicker();

    const button = await waitForElement(
      wrapper,
      'button[data-testid="select"]',
    );
    assert.isTrue(button.prop('disabled'));
  });

  it('enables "Select" button when a file is selected', async () => {
    const wrapper = renderFilePicker();

    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onSelectDocument')({ id: 123 });
    wrapper.update();

    assert.equal(
      wrapper.find('button[data-testid="select"]').prop('disabled'),
      false,
    );
  });

  it('chooses selected file when uses clicks "Select" button', async () => {
    const onSelectFile = sinon.stub();
    const wrapper = renderFilePicker({ onSelectFile });

    const file = { id: 123 };

    const fileList = await waitForElement(wrapper, 'DocumentList');
    fileList.prop('onSelectDocument')(file);
    wrapper.update();

    wrapper.find('button[data-testid="select"]').prop('onClick')();

    assert.calledWith(onSelectFile, file);
  });

  it('does not render anything while fetching', async () => {
    const wrapper = renderFilePicker();
    // Note: this passes because `FullScreenSpinner` is mocked. However, the
    // test accomplishes what it's trying to accomplish: we're not rendering
    // the Modal
    assert.isTrue(wrapper.isEmptyRender());
    assert.isTrue(wrapper.find('SpinnerOverlay').exists());

    await waitForElement(wrapper, 'DocumentList');
    assert.isFalse(wrapper.isEmptyRender());
  });

  describe('when no files are provided', () => {
    const getNoFilesMessage = async ({
      changeToSubfolder,
      documentType = 'file',
    } = {}) => {
      const wrapper = renderFilePicker({
        withBreadcrumbs: changeToSubfolder,
        documentType,
      });
      let fileList = await waitForElement(
        wrapper,
        'DocumentList[isLoading=false]',
      );

      if (changeToSubfolder) {
        changePath(wrapper, fakeFolders[0]);
        fileList = await waitForElement(wrapper, 'DocumentList');
      }

      return fileList.prop('noDocumentsMessage');
    };

    beforeEach(() => {
      fakeApiCall = sinon.stub().resolves([]); // no files returned
    });

    it('renders no-file message with a help link', async () => {
      const { props } = await getNoFilesMessage();

      assert.equal(props.href, 'https://fake_help_link');
      // After first file fetch, we're at the top level, so the no-files message
      // should operate in its "course" context
      assert.isFalse(props.inSubfolder);
    });

    it('renders no-file message in folder context if in a subfolder', async () => {
      const { props } = await getNoFilesMessage({ changeToSubfolder: true });

      // After changing path, we're in a subfolder, so the no-files message should
      // operate in its "folder" context
      assert.isTrue(props.inSubfolder);
    });

    [
      {
        options: { documentType: 'page' },
        expectedContent:
          'There are no pages in this course. Create some pages in the course and try again.',
      },
      {
        options: { documentType: 'file' },
        expectedContent:
          'There are no files in this course. Upload some files to the course and try again.',
      },
      {
        options: { documentType: 'file', changeToSubfolder: true },
        expectedContent:
          'There are no files in this folder. Upload some files to the folder and try again.',
      },
    ].forEach(({ options, expectedContent }) => {
      it('renders no-file message with expected content', async () => {
        const noFilesMessage = await getNoFilesMessage(options);
        const wrapper = mount(noFilesMessage);

        assert.equal(wrapper.text(), expectedContent);
      });
    });
  });
});
