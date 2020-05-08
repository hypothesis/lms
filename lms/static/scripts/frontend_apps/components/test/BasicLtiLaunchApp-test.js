import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import { Config } from '../../config';
import { ApiError } from '../../utils/api';

import BasicLtiLaunchApp, { $imports } from '../BasicLtiLaunchApp';
import { checkAccessibility } from '../../../test-util/accessibility';
import {
  waitFor,
  waitForElement,
  waitForElementToRemove,
} from '../../../test-util/wait';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('BasicLtiLaunchApp', () => {
  let fakeApiCall;
  let FakeAuthWindow;
  let fakeConfig;
  let fakeHypothesisConfig;
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
        <BasicLtiLaunchApp rpcServer={fakeRpcServer} {...props} />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
      canvas: {
        authUrl: 'https://lms.hypothes.is/authorize-lms',
      },
      urls: {},
      grading: {},
    };
    fakeApiCall = sinon.stub();
    FakeAuthWindow = sinon.stub().returns({
      authorize: sinon.stub().resolves(null),
    });
    fakeRpcServer = {
      resolveGroupFetch: sinon.stub(),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      './Dialog': FakeDialog,
      '../utils/AuthWindow': FakeAuthWindow,
      '../utils/api': {
        apiCall: fakeApiCall,
      },
    });

    // fake js-config
    fakeHypothesisConfig = sinon.stub(document, 'querySelector');
    fakeHypothesisConfig
      .withArgs('.js-config')
      .returns({ text: JSON.stringify({}) });
  });

  afterEach(() => {
    $imports.$restore();
    fakeHypothesisConfig.restore();
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
      const wrapper = renderLtiLaunchApp({ rpcServer: fakeRpcServer });
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
      assert.isTrue(wrapper.exists('Spinner'));
    });

    it('passes the groups array from api call to rpcServer.resolveGroupFetch', async () => {
      const promise = fakeApiCall.resolves(['group1', 'group2']);
      renderLtiLaunchApp({ rpcServer: fakeRpcServer });
      await promise;
      assert.calledWith(fakeRpcServer.resolveGroupFetch, ['group1', 'group2']);
    });
  });

  context('when a content URL callback is provided in the config', () => {
    beforeEach(() => {
      fakeConfig.api.viaCallbackUrl = 'https://lms.hypothes.is/api/files/1234';
    });

    it('attempts to fetch the content URL when mounted', async () => {
      const wrapper = renderLtiLaunchApp();

      await waitFor(() => fakeApiCall.called);

      assert.calledWith(fakeApiCall, {
        authToken: 'dummyAuthToken',
        path: 'https://lms.hypothes.is/api/files/1234',
      });
      assert.isTrue(wrapper.exists('Spinner'));
    });

    it('displays the content URL in an iframe if successfully fetched', async () => {
      fakeApiCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });

      const wrapper = renderLtiLaunchApp();

      const iframe = await waitForElement(wrapper, 'iframe');

      assert.include(iframe.props(), {
        src: 'https://via.hypothes.is/123',
      });
    });

    it('displays authorization prompt if content URL fetch fails with an `ApiError`', async () => {
      // Make the initial URL fetch request reject with an unspecified `ApiError`.
      fakeApiCall.rejects(new ApiError(400, {}));

      const wrapper = renderLtiLaunchApp();

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
      assert.called(FakeAuthWindow);

      // Check that files are fetched after authorization completes.
      const iframe = await waitForElement(wrapper, 'iframe');

      assert.equal(iframe.prop('src'), 'https://via.hypothes.is/123');
    });

    [
      {
        description: 'a specific server error',
        error: new ApiError(400, { error_message: 'Server error' }),
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

        // Verify that a "Try again" prompt is shown.
        const tryAgainButton = await waitForElement(
          wrapper,
          'Button[label="Try again"]'
        );
        assert.isTrue(tryAgainButton.exists());

        // Click the "Try again" button and verify that authorization is attempted.
        fakeApiCall.reset();
        fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
        tryAgainButton.prop('onClick')();
        assert.called(FakeAuthWindow);

        // Check that files are fetched after authorization completes.
        const iframe = await waitForElement(wrapper, 'iframe');
        assert.equal(iframe.prop('src'), 'https://via.hypothes.is/123');
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
      // needs a viaUrl or viaCallbackUrl to show iframe
      fakeConfig.viaUrl = 'https://via.hypothes.is/123';
    });

    it('renders the LMSGrader component', () => {
      const wrapper = renderLtiLaunchApp();
      const LMSGrader = wrapper.find('LMSGrader');
      assert.isTrue(LMSGrader.exists());
    });
  });

  describe('concurrent fetching of groups and content', () => {
    let contentUrlCall;
    let groupsCall;

    beforeEach(() => {
      // Will attempt to fetch the 1. content url and 2. groups.
      fakeConfig.api = {
        authToken: 'dummyAuthToken',
        viaCallbackUrl: 'https://lms.hypothes.is/api/files/1234',
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
      contentUrlCall = fakeApiCall.withArgs({
        authToken: 'dummyAuthToken',
        path: 'https://lms.hypothes.is/api/files/1234',
      });

      groupsCall = fakeApiCall.withArgs({
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

    it('renders the spinner until both groups and contentUrl requests finish', async () => {
      const contentUrl = contentUrlCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });
      const groups = groupsCall.resolves(['group1', 'group2']);
      const wrapper = renderLtiLaunchApp();
      await contentUrl;
      // Spinner should not go away after first request
      wrapper.update();
      assert.isTrue(wrapper.find('Spinner').exists());
      await groups;
      // Spinner should go away after the second request
      await waitForElementToRemove(wrapper, 'Spinner');
      // iframe should be visible
      assert.equal(wrapper.find('iframe').prop('style').visibility, 'visible');
    });

    it('renders the iframe hidden after contentUrl succeeds and groups remains pending', async () => {
      const contentUrl = contentUrlCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });
      const wrapper = renderLtiLaunchApp();
      await contentUrl;
      wrapper.update();
      assert.equal(wrapper.find('iframe').prop('style').visibility, 'hidden');
    });

    it('shows an error dialog if the first request fails and second succeeds', async () => {
      const contentUrl = contentUrlCall.rejects(new ApiError(400, {}));
      const groups = groupsCall.resolves(['group1', 'group2']);
      const wrapper = renderLtiLaunchApp();
      await contentUrl;
      // Should show an error after the first request fails
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');
      await groups;
      // Should still show an error even if the second request does not fail
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');
    });

    it('shows an error dialog if the first request succeeds and second fails', async () => {
      const contentUrl = contentUrlCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });
      const groups = groupsCall.rejects(new ApiError(400, {}));
      const wrapper = renderLtiLaunchApp();
      await contentUrl;
      // Should not show an error yet
      assert.isFalse(
        wrapper.find('FakeDialog[title="Authorize Hypothesis"]').exists()
      );
      await groups;
      // Should show an error after failure
      await waitForElement(wrapper, 'FakeDialog[title="Authorize Hypothesis"]');
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
