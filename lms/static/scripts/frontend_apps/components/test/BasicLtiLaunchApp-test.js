import { mount } from 'enzyme';
import { Fragment, createElement } from 'preact';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { ApiError } from '../../utils/api';

import BasicLtiLaunchApp, { $imports } from '../BasicLtiLaunchApp';
import { checkAccessibility } from '../../../test-util/accessibility';
import { waitFor, waitForElement } from '../../../test-util/wait';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('BasicLtiLaunchApp', () => {
  let fakeApiCall;
  let FakeAuthWindow;
  let fakeConfig;
  let fakeRpcServer;

  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ buttons, children }) => (
    <Fragment>
      {buttons} {children}
    </Fragment>
  );

  const renderLtiLaunchApp = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <BasicLtiLaunchApp clientRpc={fakeRpcServer} {...props} />
      </Config.Provider>
    );
  };

  function spinnerVisible(wrapper) {
    return waitForElement(wrapper, 'Spinner');
  }

  function spinnerHidden(wrapper) {
    return waitFor(() => {
      wrapper.update();
      return !wrapper.exists('Spinner');
    });
  }

  function contentHidden(wrapper) {
    return waitForElement(wrapper, '.BasicLtiLaunchApp__content.is-hidden');
  }

  function contentVisible(wrapper) {
    return waitForElement(
      wrapper,
      '.BasicLtiLaunchApp__content:not(.is-hidden)'
    );
  }

  beforeEach(() => {
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      canvas: {},
      urls: {},
      grading: {},
    };
    fakeApiCall = sinon.stub();
    FakeAuthWindow = sinon.stub().returns({
      authorize: sinon.stub().resolves(null),
      focus: sinon.stub(),
    });
    fakeRpcServer = {
      setGroups: sinon.stub(),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      './Dialog': FakeDialog,
      '../utils/AuthWindow': FakeAuthWindow,
      '../utils/api': {
        apiCall: fakeApiCall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  context('when a content URL is provided in the config', () => {
    beforeEach(() => {
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('displays the content URL in an iframe', () => {
      const wrapper = renderLtiLaunchApp();

      const iframe = wrapper.find('iframe');
      assert.isTrue(iframe.exists());
      assert.include(iframe.props(), {
        src: 'https://via.hypothes.is/123',
      });
    });
  });

  context('when `sync` object is provided in the config', () => {
    beforeEach(() => {
      fakeConfig.api.sync = {
        data: {
          course: {
            context_id: '12345',
            custom_canvas_course_id: '101',
          },
        },
        path: '/api/sync',
      };
    });

    it('attempts to fetch the groups when mounted', async () => {
      renderLtiLaunchApp({ rpcServer: fakeRpcServer });
      await waitFor(() => fakeApiCall.called);
      assert.calledWith(fakeApiCall, {
        authToken: 'dummyAuthToken',
        path: '/api/sync',
        data: {
          course: {
            context_id: '12345',
            custom_canvas_course_id: '101',
          },
        },
      });
    });

    it('passes the groups array from api call to rpcServer.setGroups', async () => {
      const groups = await fakeApiCall.resolves(['group1', 'group2']);
      renderLtiLaunchApp();
      await groups;
      assert.calledWith(fakeRpcServer.setGroups, ['group1', 'group2']);
    });
  });

  context('when a content URL callback is provided in the config', () => {
    const authUrl = 'https://lms.hypothes.is/authorize-lms';

    beforeEach(() => {
      fakeConfig.api.viaUrl = {
        authUrl,
        path: 'https://lms.hypothes.is/api/files/1234',
      };
    });

    it('attempts to fetch the content URL when mounted', async () => {
      const wrapper = renderLtiLaunchApp();
      await spinnerVisible(wrapper);
      await waitFor(() => fakeApiCall.called);

      assert.calledWith(fakeApiCall, {
        authToken: 'dummyAuthToken',
        path: 'https://lms.hypothes.is/api/files/1234',
      });
      await spinnerHidden(wrapper);
    });

    it('displays the content URL in an iframe if successfully fetched', async () => {
      fakeApiCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });

      const wrapper = renderLtiLaunchApp();
      await contentVisible(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123'
      );
    });

    it('displays authorization prompt if content URL fetch fails with an `ApiError`', async () => {
      // Make the initial URL fetch request reject with an unspecified `ApiError`.
      fakeApiCall.rejects(new ApiError(400, {}));

      const wrapper = renderLtiLaunchApp();
      await spinnerVisible(wrapper);
      // Verify that an "Authorize" prompt is shown.
      const authButton = await waitForElement(
        wrapper,
        'Button[label="Authorize"]'
      );
      assert.isTrue(authButton.exists());

      // Click the "Authorize" button and verify that authorization is attempted.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      authButton.prop('onClick')();
      assert.calledWith(FakeAuthWindow, {
        authToken: 'dummyAuthToken',
        authUrl,
      });

      // Check that files are fetched after authorization completes.
      await contentVisible(wrapper);
      await spinnerHidden(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123'
      );
    });

    it('does not create a second auth window when Authorize button is clicked twice', async () => {
      // Make the initial URL fetch request reject with an unspecified `ApiError`.
      fakeApiCall.rejects(new ApiError(400, {}));

      const wrapper = renderLtiLaunchApp();
      const authButton = await waitForElement(
        wrapper,
        'Button[label="Authorize"]'
      );

      // Click the "Authorize" button
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });

      act(() => {
        authButton.prop('onClick')();
      });
      assert.calledOnce(FakeAuthWindow);

      // Click the "Authorize" button again
      act(() => {
        authButton.prop('onClick')();
      });
      assert.calledOnce(FakeAuthWindow);
    });

    [
      {
        description: 'a specific server error',
        error: new ApiError(400, { message: 'Server error' }),
      },
      {
        description: 'a network or other generic error',
        error: new Error('Failed to fetch'),
      },
    ].forEach(({ description, error }) => {
      it(`displays error details if content URL fetch fails with ${description}`, async () => {
        // Make the initial URL fetch request reject with the given error.
        fakeApiCall.rejects(error);

        const wrapper = renderLtiLaunchApp();
        await spinnerVisible(wrapper);

        // Verify that a "Try again" prompt is shown.
        const tryAgainButton = await waitForElement(
          wrapper,
          'Button[label="Try again"]'
        );

        // Click the "Try again" button and verify that authorization is attempted.
        fakeApiCall.reset();
        fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
        tryAgainButton.prop('onClick')();
        assert.called(FakeAuthWindow);

        // Check that files are fetched after authorization completes.
        await contentVisible(wrapper);
        await spinnerHidden(wrapper);
        assert.equal(
          wrapper.find('iframe').prop('src'),
          'https://via.hypothes.is/123'
        );
      });
    });
  });

  describe('speed grader config', () => {
    beforeEach(() => {
      fakeConfig.canvas.speedGrader = {
        submissionParams: {
          lis_result_sourcedid: 'modelstudent-assignment1',
        },
      };
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('reports the submission when the content iframe starts loading', async () => {
      const wrapper = renderLtiLaunchApp();
      await waitFor(() => fakeApiCall.called);

      assert.calledWith(fakeApiCall, {
        authToken: 'dummyAuthToken',
        path: '/api/lti/submissions',
        data: fakeConfig.canvas.speedGrader.submissionParams,
      });

      // After the successful API call, the iframe should still be rendered.
      wrapper.update();
      assert.isTrue(wrapper.exists('iframe'));
    });

    it('displays an error if reporting the submission fails', async () => {
      const error = new ApiError(400, {});
      fakeApiCall.rejects(error);

      const wrapper = renderLtiLaunchApp();

      // Wait for the API call to fail and check that an error is displayed.
      const errorDisplay = await waitForElement(wrapper, 'ErrorDisplay');
      assert.equal(errorDisplay.prop('error'), error);

      // There should be no "Try again" button in this context, instead we just
      // ask the user to reload the page.
      const tryAgainButton = wrapper.find('Button[label="Try again"]');
      assert.isFalse(tryAgainButton.exists());
      assert.include(
        wrapper.text(),
        'To fix this problem, try reloading the page'
      );
    });

    it('does not report a submission if a teacher launches an assignment', async () => {
      // When a teacher launches the assignment, there will typically be no
      // `submissionParams` config provided by the backend.
      fakeConfig.canvas.speedGrader.submissionParams = undefined;

      renderLtiLaunchApp();
      await new Promise(resolve => setTimeout(resolve, 0));

      assert.notCalled(fakeApiCall);
    });

    it('does not report a submission if `speedGrader` object is omitted', async () => {
      fakeConfig.canvas.speedGrader = undefined;

      renderLtiLaunchApp();
      await new Promise(resolve => setTimeout(resolve, 0));

      assert.notCalled(fakeApiCall);
    });

    it('does not report the submission when there is no `contentUrl`', async () => {
      // When present, viaUrl becomes the contentUrl
      fakeConfig.viaUrl = null;
      renderLtiLaunchApp();
      assert.isTrue(fakeApiCall.notCalled);
    });
  });

  context('when grading is enabled', () => {
    beforeEach(() => {
      fakeConfig.grading = {
        enabled: true,
        students: [{ userid: 'user1' }, { userid: 'user2' }],
      };
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('renders the LMSGrader component', () => {
      const wrapper = renderLtiLaunchApp();
      const LMSGrader = wrapper.find('LMSGrader');
      assert.isTrue(LMSGrader.exists());
    });
  });

  describe('concurrent fetching of groups and content', () => {
    let contentUrlResolve;
    let contentUrlReject;
    let groupsCallResolve;
    let groupsCallReject;

    const resetApiCalls = () => {
      fakeApiCall
        .withArgs({
          authToken: 'dummyAuthToken',
          path: 'https://lms.hypothes.is/api/files/1234',
        })
        .returns(
          new Promise((resolve, reject) => {
            contentUrlResolve = resolve;
            contentUrlReject = reject;
          })
        );

      fakeApiCall
        .withArgs({
          authToken: 'dummyAuthToken',
          path: '/api/sync',
          data: {
            course: {
              context_id: '12345',
              custom_canvas_course_id: '101',
            },
          },
        })
        .returns(
          new Promise((resolve, reject) => {
            groupsCallResolve = resolve;
            groupsCallReject = reject;
          })
        );
    };

    beforeEach(() => {
      // When BasicLtiLaunchApp is rendered, it will attempt to fetch:
      //  1. content url
      //  2. groups
      fakeConfig.api = {
        authToken: 'dummyAuthToken',
        viaUrl: {
          authUrl: 'https://lms.hypothes.is/authorize-lms',
          path: 'https://lms.hypothes.is/api/files/1234',
        },
        sync: {
          data: {
            course: {
              context_id: '12345',
              custom_canvas_course_id: '101',
            },
          },
          path: '/api/sync',
        },
      };
      resetApiCalls();
    });

    it('renders the spinner until contentUrl requests finish', async () => {
      const wrapper = renderLtiLaunchApp();
      // Spinner should not go away if only the groups resolves
      groupsCallResolve(['group1', 'group2']);
      await spinnerVisible(wrapper);

      // Spinner shall hide after content url resolves
      contentUrlResolve({
        via_url: 'https://via.hypothes.is/123',
      });
      await spinnerHidden(wrapper);
      await contentVisible(wrapper);
    });

    it('renders the iframe after contentUrl succeeds but groups remains pending', async () => {
      const wrapper = renderLtiLaunchApp();
      contentUrlResolve({
        via_url: 'https://via.hypothes.is/123',
      });
      await contentVisible(wrapper);
    });

    it('shows an error dialog if the first request fails and second succeeds', async () => {
      const wrapper = renderLtiLaunchApp();
      // Should show an error after the first request fails
      contentUrlReject(new ApiError(400, {}));
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');

      // Should still show an error even if the second request does not fail
      groupsCallResolve(['group1', 'group2']);
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');
      await contentHidden(wrapper);
    });

    it('shows an error dialog if the first request succeeds and second fails', async () => {
      const wrapper = renderLtiLaunchApp();
      // Should not show an error yet
      contentUrlResolve({
        via_url: 'https://via.hypothes.is/123',
      });
      await contentVisible(wrapper);

      // Should show an error after failure
      groupsCallReject(new ApiError(400, {}));
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');
      await contentHidden(wrapper);
    });

    context('when auth fails multiple times in a row', () => {
      // Helper to ensure the dialog is initially present but also remains so
      // for a short duration longer without disappearing.
      async function dialogShouldRemain(wrapper) {
        // Error prompt should be present.
        assert.isTrue(wrapper.find('FakeDialog').exists());
        // Error prompt should also not go away after a short while (see issue #1826)
        try {
          await waitFor(() => {
            wrapper.update();
            if (!wrapper.exists('FakeDialog')) {
              throw new Error();
            }
            return null;
          }, 10);
        } catch (e) {
          if (!e.message) {
            throw new Error('The dialog disappeared');
          }
        }
      }

      it('shows an error dialog if the initial content/groups requests reject and second attempt also rejects', async () => {
        const wrapper = renderLtiLaunchApp();
        // Both requests reject first
        contentUrlReject(new ApiError(400, {}));
        groupsCallReject(new ApiError(400, {}));

        const authButton = await waitForElement(
          wrapper,
          'Button[label="Authorize"]'
        );
        resetApiCalls();
        await dialogShouldRemain(wrapper);
        // contentUrlReject rejects again
        contentUrlReject(new ApiError(400, {}));
        groupsCallReject(new ApiError(400, {}));
        // Click the "Authorize" button.
        authButton.prop('onClick')();
        // Dialog prompt should remain.
        await dialogShouldRemain(wrapper);
      });

      it('shows an error dialog if contentUrl succeeds but groups rejects first', async () => {
        const wrapper = renderLtiLaunchApp();
        // Both requests reject first
        contentUrlReject(new ApiError(400, {}));
        groupsCallReject(new ApiError(400, {}));

        const authButton = await waitForElement(
          wrapper,
          'Button[label="Authorize"]'
        );
        resetApiCalls();
        // groups still fails, but contentUrl does not.
        groupsCallReject(new ApiError(400, {}));
        // Click the "Authorize" button.
        authButton.prop('onClick')();
        // Dialog prompt should remain.
        await dialogShouldRemain(wrapper);
      });

      it('disables "Authorize" button while re-fetching content and groups', async () => {
        const wrapper = renderLtiLaunchApp();

        // Make initial content URL and groups requests fail.
        contentUrlReject(new ApiError(400, {}));
        groupsCallReject(new ApiError(400, {}));

        resetApiCalls();

        // Click the "Authorize" button.
        const authButton = await waitForElement(
          wrapper,
          'Button[label="Authorize"]'
        );
        authButton.prop('onClick')();

        // Wait for the "Authorize" button to appear disabled.
        await waitFor(() => {
          wrapper.update();
          return wrapper.find('Button[label="Authorize"]').prop('disabled');
        });

        // Let the content URL fetch complete and wait a moment.
        // The "Authorize" button should remain disabled.
        contentUrlResolve({
          via_url: 'https://via.hypothes.is/123',
        });

        await new Promise(resolve => setTimeout(resolve, 1));
        wrapper.update();
        assert.isTrue(
          wrapper.find('Button[label="Authorize"]').prop('disabled')
        );

        // Let the groups fetch complete. The content should then appear.
        groupsCallResolve(['group1', 'group2']);
        await contentVisible(wrapper);
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        content: () => {
          fakeConfig = {
            ...fakeConfig,
            viaUrl: 'https://via.hypothes.is/123',
          };
          return renderLtiLaunchApp();
        },
      },
      {
        name: 'LMS grader mode',
        content: () => {
          // Turn on grading for this test. Note: fakeConfig won't
          // reset for a successive axe test, so its important that this
          // test is the last one run in the test list. Otherwise
          // fakeConfig will need to be restored again as done in the
          // root level beforeEach() at the top of the file.
          fakeConfig = {
            ...fakeConfig,
            grading: {
              enabled: true,
              students: [],
              courseName: 'courseName',
              assignmentName: 'assignmentName',
            },
          };
          return renderLtiLaunchApp();
        },
      },
    ])
  );
});
