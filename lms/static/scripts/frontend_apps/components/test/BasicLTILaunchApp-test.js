import {
  checkAccessibility,
  mockImportedComponents,
  delay,
  waitFor,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { APIError } from '../../errors';
import { ClientRPC, Services } from '../../services';
import BasicLTILaunchApp, { $imports } from '../BasicLTILaunchApp';

describe('BasicLTILaunchApp', () => {
  let fakeApiCall;
  let FakeAuthWindow;
  let fakeConfig;
  let fakeRpcServer;

  const renderLTILaunchApp = (props = {}) => {
    const services = new Map([[ClientRPC, fakeRpcServer]]);
    return mount(
      <Config.Provider value={fakeConfig}>
        <Services.Provider value={services}>
          <BasicLTILaunchApp {...props} />
        </Services.Provider>
      </Config.Provider>,
    );
  };

  function spinnerVisible(wrapper) {
    return waitForElement(wrapper, 'SpinnerOverlay');
  }

  function spinnerHidden(wrapper) {
    return waitFor(() => {
      wrapper.update();
      return !wrapper.exists('SpinnerOverlay');
    });
  }

  function contentHidden(wrapper) {
    return waitForElement(wrapper, '[data-testid="content-wrapper"].invisible');
  }

  function contentVisible(wrapper) {
    return waitForElement(wrapper, '[data-testid="content-wrapper"].visible');
  }

  beforeEach(() => {
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      canvas: {},
      hypothesisClient: {},
      urls: {},
    };
    fakeApiCall = sinon.stub();
    FakeAuthWindow = sinon.stub().returns({
      authorize: sinon.stub().resolves(null),
      focus: sinon.stub(),
    });
    fakeRpcServer = {
      on: sinon.stub(),
      off: sinon.stub(),
      setGroups: sinon.stub(),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      // Don't mock `ContentFrame`. It is a trivial iframe wrapper.
      './ContentFrame': true,
    });
    $imports.$mock({
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
      const wrapper = renderLTILaunchApp();

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
      renderLTILaunchApp({ rpcServer: fakeRpcServer });
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
      renderLTILaunchApp();
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
      const wrapper = renderLTILaunchApp();
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

      const wrapper = renderLTILaunchApp();
      await contentVisible(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123',
      );
    });

    it('displays authorization prompt if content URL fetch fails and we can re-authorize', async () => {
      // Make the initial URL fetch request reject with an unspecified `APIError`.
      fakeApiCall.rejects(new APIError(400, {}));

      const wrapper = renderLTILaunchApp();
      await spinnerVisible(wrapper);
      // Verify that an "Authorize" prompt is shown.
      const errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-authorizing"]',
      );

      // Click the "Authorize" button and verify that authorization is attempted.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledWith(FakeAuthWindow, {
        authToken: 'dummyAuthToken',
        authUrl,
      });

      // Check that files are fetched after authorization completes.
      await contentVisible(wrapper);
      await spinnerHidden(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123',
      );
    });

    it('does not create a second auth window when Authorize button is clicked twice', async () => {
      // Make the initial URL fetch request reject with an unspecified `APIError`.
      fakeApiCall.rejects(new APIError(400, {}));

      const wrapper = renderLTILaunchApp();
      const errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-authorizing"]',
      );

      // Click the "Authorize" button
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });

      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledOnce(FakeAuthWindow);

      // Click the "Authorize" button again
      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledOnce(FakeAuthWindow);
    });

    [
      {
        description: 'a specific server error',
        error: new APIError(400, { message: 'Server error' }),
        authUrl,
      },
      {
        description: 'a specific server error',
        error: new APIError(409, { message: 'Something went wrong' }),
        authUrl: null,
      },
      {
        description: 'a network or other generic error',
        error: new Error('Failed to fetch'),
        authUrl,
      },
    ].forEach(({ description, error, authUrl }) => {
      it(`displays error details and allows retry if content URL fetch fails (${description})`, async () => {
        // Make the initial URL fetch request reject with the given error.
        fakeApiCall.rejects(error);
        fakeConfig.api.viaUrl.authUrl = authUrl;

        const wrapper = renderLTILaunchApp();
        await spinnerVisible(wrapper);

        // Verify that an "Try again" prompt is shown.
        let errorDialog = await waitForElement(wrapper, 'LaunchErrorDialog');

        // Click the "Try again" button. If re-authorization is available /
        // appropriate we should re-launch the auth flow. Otherwise we should
        // just retry fetching the content URL.
        fakeApiCall.reset();
        fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
        act(() => {
          errorDialog.prop('onRetry')();
        });
        wrapper.update();
        errorDialog = wrapper.find('LaunchErrorDialog');

        if (authUrl) {
          assert.equal(errorDialog.prop('errorState'), 'error-authorizing');
          assert.called(FakeAuthWindow);
        } else {
          assert.notEqual(errorDialog.prop('errorState'), 'error-authorizing');
          assert.notCalled(FakeAuthWindow);
        }

        // Check that files are fetched after authorization completes.
        await contentVisible(wrapper);
        await spinnerHidden(wrapper);
        assert.equal(
          wrapper.find('iframe').prop('src'),
          'https://via.hypothes.is/123',
        );
      });
    });

    it('shows Canvas file permission error if content URL fetch fails with "canvas_api_permission_error" error', async () => {
      // Make the initial URL fetch request reject with a Canvas API permission error.
      fakeApiCall.rejects(
        new APIError(400, { error_code: 'canvas_api_permission_error' }),
      );

      const wrapper = renderLTILaunchApp();
      await spinnerVisible(wrapper);

      // Verify that the expected error dialog is shown.
      let errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="canvas_api_permission_error"]',
      );

      // Click the "Try again" button. This should re-authorize and then re-fetch files.
      fakeApiCall.resetHistory();
      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledWith(FakeAuthWindow, {
        authToken: 'dummyAuthToken',
        authUrl,
      });
      await waitFor(() => fakeApiCall.called);

      // We didn't change the API response, so it will fail the same way and the same error dialog
      // should be shown.
      errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="canvas_api_permission_error"]',
      );

      // Change the API call to succeed and try again.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      act(() => {
        errorDialog.prop('onRetry')();
      });

      // When the request succeeds, the content should now be shown.
      await contentVisible(wrapper);
      await spinnerHidden(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123',
      );
    });

    it('shows Canvas file not found in course error if content URL fetch fails with "canvas_file_not_found_in_course" error', async () => {
      // Make the initial URL fetch request reject with a Canvas API permission error.
      fakeApiCall.rejects(
        new APIError(400, { error_code: 'canvas_file_not_found_in_course' }),
      );

      const wrapper = renderLTILaunchApp();
      await spinnerVisible(wrapper);

      // Verify that the expected error dialog is shown.
      let errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="canvas_file_not_found_in_course"]',
      );

      // Click the "Try again" button. This should re-authorize and then re-fetch files.
      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledWith(FakeAuthWindow, {
        authToken: 'dummyAuthToken',
        authUrl,
      });
      await waitFor(() => fakeApiCall.called);

      // We didn't change the API response, so it will fail the same way and the same error dialog
      // should be shown.
      errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="canvas_file_not_found_in_course"]',
      );

      // Change the API call to succeed and try again.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      act(() => {
        errorDialog.prop('onRetry')();
      });

      // When the request succeeds, the content should now be shown.
      await contentVisible(wrapper);
      await spinnerHidden(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123',
      );
    });

    it('shows Blackboard file not found in course error if content URL fetch fails with "blackboard_file_not_found_in_course" error', async () => {
      // Make the initial URL fetch request reject with a Blackboard API permission error.
      fakeApiCall.rejects(
        new APIError(400, {
          error_code: 'blackboard_file_not_found_in_course',
        }),
      );

      const wrapper = renderLTILaunchApp();
      await spinnerVisible(wrapper);

      // Verify that the expected error dialog is shown.
      let errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="blackboard_file_not_found_in_course"]',
      );

      // Click the "Try again" button. This should re-authorize and then re-fetch files.
      act(() => {
        errorDialog.prop('onRetry')();
      });
      assert.calledWith(FakeAuthWindow, {
        authToken: 'dummyAuthToken',
        authUrl,
      });
      await waitFor(() => fakeApiCall.called);

      // We didn't change the API response, so it will fail the same way and the same error dialog
      // should be shown.
      errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="blackboard_file_not_found_in_course"]',
      );

      // Change the API call to succeed and try again.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      act(() => {
        errorDialog.prop('onRetry')();
      });

      // When the request succeeds, the content should now be shown.
      await contentVisible(wrapper);
      await spinnerHidden(wrapper);
      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123',
      );
    });
  });

  describe('Canvas speed grader integration', () => {
    beforeEach(() => {
      fakeConfig.canvas.speedGrader = {
        submissionParams: {
          lis_result_sourcedid: 'modelstudent-assignment1',
        },
      };
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('reports the submission when the content iframe starts loading', async () => {
      const wrapper = renderLTILaunchApp();
      await waitFor(() => fakeApiCall.called);

      const apiCall = fakeApiCall.getCall(0);
      assert.deepEqual(apiCall.args[0], {
        authToken: 'dummyAuthToken',
        path: '/api/lti/submissions',
        data: {
          submitted_at: undefined,
          ...fakeConfig.canvas.speedGrader.submissionParams,
        },
      });

      // After the successful API call, the iframe should still be rendered.
      wrapper.update();
      assert.isTrue(wrapper.exists('iframe'));
    });

    // Make the grading submission API call fail.
    function makeSubmissionFail() {
      const error = new APIError(400, {});
      fakeApiCall
        .withArgs(sinon.match({ path: '/api/lti/submissions' }))
        .rejects(error);
      return error;
    }

    async function waitForErrorDialog(wrapper) {
      // Wait for the API call to fail and check that an error is displayed.
      // There should be no "Try again" button in this context, instead we just
      // ask the user to reload the page.
      const errorDialog = await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-reporting-submission"]',
      );
      return errorDialog;
    }

    it('displays an error if reporting the submission fails', async () => {
      const error = makeSubmissionFail();
      const wrapper = renderLTILaunchApp();
      const errorDialog = await waitForErrorDialog(wrapper);
      assert.equal(errorDialog.prop('error'), error);
    });

    it('allows user to dismiss error', async () => {
      makeSubmissionFail();
      const wrapper = renderLTILaunchApp();
      const errorDialog = await waitForErrorDialog(wrapper);

      errorDialog.prop('onDismiss')();
      wrapper.update();

      assert.isFalse(wrapper.exists('LaunchErrorDialog'));
    });

    it('does not report a submission if grading is not enabled for the current user', async () => {
      // If the assignment is not gradable or the user is an instructor, the
      // `speedGrader` config is omitted.
      fakeConfig.canvas.speedGrader = undefined;

      renderLTILaunchApp();
      await new Promise(resolve => setTimeout(resolve, 0));

      assert.notCalled(fakeApiCall);
    });

    it('does not report the submission when there is no `viaUrl` provided', async () => {
      // When present, viaUrl becomes the contentUrl
      fakeConfig.viaUrl = null;
      renderLTILaunchApp();
      assert.isTrue(fakeApiCall.notCalled);
    });

    context(
      'When configured to wait for first annotation activity before submission',
      () => {
        beforeEach(() => {
          fakeConfig.canvas.speedGrader = {
            submissionParams: {
              lis_result_sourcedid: 'modelstudent-assignment1',
            },
          };
          fakeConfig.viaUrl = 'https://via.hypothes.is/123';
          fakeConfig.hypothesisClient.reportActivity = {
            method: 'reportActivity',
            events: ['create', 'edit'],
          };
        });

        function getOnActivityCalls(stub) {
          return stub
            .getCalls()
            .filter(call => call.args[0] === 'annotationActivity');
        }

        it('does not report the submission when the content iframe starts loading', async () => {
          const wrapper = renderLTILaunchApp();
          await new Promise(resolve => setTimeout(resolve, 1));
          assert.isFalse(
            fakeApiCall.calledWith(
              sinon.match({ path: '/api/lti/submissions' }),
            ),
          );

          // After the successful API call, the iframe should still be rendered.
          wrapper.update();
          assert.isTrue(wrapper.exists('iframe'));
        });

        it('registers a callback for `annotationActivity` events', async () => {
          renderLTILaunchApp();
          const annotationActivityCalls = getOnActivityCalls(fakeRpcServer.on);
          assert.equal(annotationActivityCalls.length, 1);
          assert.isFunction(annotationActivityCalls[0].args[1]);
        });

        // Simulate annotation activity being reported from the client to the
        // LMS frontend.
        async function reportActivity() {
          const annotationActivityCalls = getOnActivityCalls(fakeRpcServer.on);
          const callback = annotationActivityCalls[0].callback;
          callback('create', { annotation: { isShared: true } });
          await delay(0);
          return callback;
        }

        context(
          '`annotationActivity` event that qualifies for submission',
          () => {
            it('creates submission', async () => {
              renderLTILaunchApp();
              assert.isFalse(
                fakeApiCall.calledWith(
                  sinon.match({ path: '/api/lti/submissions' }),
                ),
              );

              await reportActivity();

              assert.calledOnce(fakeApiCall);
              assert.calledWith(
                fakeApiCall,
                sinon.match({ path: '/api/lti/submissions' }),
              );

              const apiCall = fakeApiCall.getCall(0);
              assert.deepEqual(apiCall.args[0], {
                authToken: 'dummyAuthToken',
                path: '/api/lti/submissions',
                data: {
                  submitted_at: undefined,
                  ...fakeConfig.canvas.speedGrader.submissionParams,
                },
              });
            });

            it('deregisters callback after submission is made', async () => {
              renderLTILaunchApp();

              const callback = await reportActivity();

              assert.calledOnce(fakeApiCall);
              assert.calledWith(
                fakeApiCall,
                sinon.match({ path: '/api/lti/submissions' }),
              );
              assert.calledOnce(fakeRpcServer.off);
              assert.calledWith(
                fakeRpcServer.off,
                'annotationActivity',
                callback,
              );
            });

            it('submits a submission with annotation-activity date if provided', async () => {
              renderLTILaunchApp();

              const annotationActivityCalls = getOnActivityCalls(
                fakeRpcServer.on,
              );
              const callback = annotationActivityCalls[0].args[1];
              assert.notCalled(fakeApiCall);
              callback('create', {
                date: '2022-04-28T13:25:34Z',
                annotation: { isShared: true },
              });

              const apiCall = fakeApiCall.getCall(0);
              assert.deepEqual(apiCall.args[0], {
                authToken: 'dummyAuthToken',
                path: '/api/lti/submissions',
                data: {
                  submitted_at: '2022-04-28T13:25:34Z',
                  ...fakeConfig.canvas.speedGrader.submissionParams,
                },
              });
            });
          },
        );

        context(
          '`annotationActivity` event that does not qualify for submission',
          () => {
            it('does not submit a submission if event type not `create` or `update`', async () => {
              renderLTILaunchApp();
              const annotationActivityCalls = getOnActivityCalls(
                fakeRpcServer.on,
              );
              const callback = annotationActivityCalls[0].callback;
              callback('delete', { annotation: { isShared: true } });
              await delay(0);

              assert.notCalled(fakeApiCall);
            });

            it('does not deregister callback on non-qualifying annotation event', async () => {
              renderLTILaunchApp();

              const annotationActivityCalls = getOnActivityCalls(
                fakeRpcServer.on,
              );
              const callback = annotationActivityCalls[0].args[1];
              callback('delete', { annotation: { isShared: true } });
              await delay(0);

              assert.notCalled(fakeRpcServer.off);
            });

            it('does not submit if annotation is not shared', async () => {
              renderLTILaunchApp();
              const annotationActivityCalls = getOnActivityCalls(
                fakeRpcServer.on,
              );
              const callback = annotationActivityCalls[0].callback;
              callback('create', { annotation: { isShared: false } });
              await delay(0);

              assert.notCalled(fakeApiCall);
            });
          },
        );
      },
    );
  });

  context('when grading is enabled', () => {
    beforeEach(() => {
      fakeConfig.grading = {
        enabled: true,
        students: [{ userid: 'user1' }, { userid: 'user2' }],
      };
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('renders the InstructorToolbar component', () => {
      const wrapper = renderLTILaunchApp();
      const InstructorToolbar = wrapper.find('InstructorToolbar');
      assert.isTrue(InstructorToolbar.exists());
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
          }),
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
          }),
        );
    };

    beforeEach(() => {
      // When BasicLTILaunchApp is rendered, it will attempt to fetch:
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
      const wrapper = renderLTILaunchApp();
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
      const wrapper = renderLTILaunchApp();
      contentUrlResolve({
        via_url: 'https://via.hypothes.is/123',
      });
      await contentVisible(wrapper);
    });

    it('shows an error dialog if the first request fails and second succeeds', async () => {
      const wrapper = renderLTILaunchApp();
      // Should show an error after the first request fails
      contentUrlReject(new APIError(400, {}));
      await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-authorizing"]',
      );

      // Should still show an error even if the second request does not fail
      groupsCallResolve(['group1', 'group2']);
      await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-authorizing"]',
      );
      await contentHidden(wrapper);
    });

    it('shows an error dialog if the first request succeeds and second fails', async () => {
      const wrapper = renderLTILaunchApp();
      // Should not show an error yet
      contentUrlResolve({
        via_url: 'https://via.hypothes.is/123',
      });
      await contentVisible(wrapper);

      // Should show an error after failure
      groupsCallReject(new APIError(400, {}));
      await waitForElement(
        wrapper,
        'LaunchErrorDialog[errorState="error-authorizing"]',
      );
    });

    context('when auth fails multiple times in a row', () => {
      // Helper to ensure the dialog is initially present but also remains so
      // for a short duration longer without disappearing.
      async function dialogShouldRemain(wrapper) {
        // Error prompt should be present.
        assert.isTrue(wrapper.find('LaunchErrorDialog').exists());
        // Error prompt should also not go away after a short while (see issue #1826)
        await delay(10);
        wrapper.update();
        if (!wrapper.exists('LaunchErrorDialog')) {
          throw new Error('The dialog disappeared');
        }
      }

      it('shows an error dialog if the initial content/groups requests reject and second attempt also rejects', async () => {
        const wrapper = renderLTILaunchApp();
        // Both requests reject first
        contentUrlReject(new APIError(400, {}));
        groupsCallReject(new APIError(400, {}));

        const errorDialog = await waitForElement(
          wrapper,
          'LaunchErrorDialog[errorState="error-authorizing"]',
        );
        resetApiCalls();
        await dialogShouldRemain(wrapper);
        // contentUrlReject rejects again
        contentUrlReject(new APIError(400, {}));
        groupsCallReject(new APIError(400, {}));
        // Click the "Authorize" button.
        act(() => {
          errorDialog.prop('onRetry')();
        });
        // Dialog prompt should remain.
        await dialogShouldRemain(wrapper);
      });

      it('shows an error dialog if contentUrl succeeds but groups rejects first', async () => {
        const wrapper = renderLTILaunchApp();
        // Both requests reject first
        contentUrlReject(new APIError(400, {}));
        groupsCallReject(new APIError(400, {}));

        const errorDialog = await waitForElement(
          wrapper,
          'LaunchErrorDialog[errorState="error-authorizing"]',
        );
        resetApiCalls();
        // groups still fails, but contentUrl does not.
        groupsCallReject(new APIError(400, {}));
        // Click the "Authorize" button.
        act(() => {
          errorDialog.prop('onRetry')();
        });
        // Dialog prompt should remain.
        await dialogShouldRemain(wrapper);
      });

      it('disables "Authorize" button while re-fetching content and groups', async () => {
        const wrapper = renderLTILaunchApp();

        // Make initial content URL and groups requests fail.
        contentUrlReject(new APIError(400, {}));
        groupsCallReject(new APIError(400, {}));

        resetApiCalls();

        // Click the "Authorize" button.
        const errorDialog = await waitForElement(
          wrapper,
          'LaunchErrorDialog[errorState="error-authorizing"]',
        );
        act(() => {
          errorDialog.prop('onRetry')();
        });

        // Wait for the "Authorize" button to appear disabled.
        await waitFor(() => {
          wrapper.update();
          return wrapper.find('LaunchErrorDialog').prop('busy');
        });

        // Let the content URL fetch complete and wait a moment.
        // The "Authorize" button should remain disabled.
        contentUrlResolve({
          via_url: 'https://via.hypothes.is/123',
        });

        await new Promise(resolve => setTimeout(resolve, 1));
        wrapper.update();
        assert.isTrue(wrapper.find('LaunchErrorDialog').prop('busy'));

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
          return renderLTILaunchApp();
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
          return renderLTILaunchApp();
        },
      },
    ]),
  );
});
