import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import { Config } from '../../config';
import { ApiError } from '../../utils/api';

import BasicLtiLaunchApp, { $imports } from '../BasicLtiLaunchApp';

import { waitFor, waitForElement } from './util';
import mockImportedComponents from './mock-imported-components';

describe('BasicLtiLaunchApp', () => {
  let fakeApiCall;
  let FakeAuthWindow;
  let fakeConfig;
  let fakeHypothesisConfig;

  // eslint-disable-next-line react/prop-types
  const FakeDialog = ({ buttons, children }) => (
    <Fragment>
      {buttons} {children}
    </Fragment>
  );

  const renderLtiLaunchApp = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <BasicLtiLaunchApp {...props} />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      authToken: 'dummyAuthToken',
      authUrl: 'https://lms.hypothes.is/authorize-lms',
      lmsName: 'Shiny LMS',
      urls: {},
    };

    fakeApiCall = sinon.stub();

    FakeAuthWindow = sinon.stub().returns({
      authorize: sinon.stub().resolves(null),
    });

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      './Dialog': FakeDialog,

      '../utils/AuthWindow': FakeAuthWindow,
      '../utils/api': {
        apiCall: fakeApiCall,
      },
    });

    // fake js-hypothesis-config
    fakeHypothesisConfig = sinon.stub(document, 'querySelector');
    fakeHypothesisConfig
      .withArgs('.js-hypothesis-config')
      .returns({ text: JSON.stringify({}) });
  });

  afterEach(() => {
    $imports.$restore();
    fakeHypothesisConfig.restore();
  });

  context('when a content URL is provided in the config', () => {
    beforeEach(() => {
      fakeConfig.urls.via_url = 'https://via.hypothes.is/123';
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

  context('when a content URL callback is provided in the config', () => {
    beforeEach(() => {
      fakeConfig.urls.via_url_callback =
        'https://lms.hypothes.is/api/files/1234';
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

  it('reports the submission in the LMS when the content iframe starts loading', async () => {
    fakeConfig.submissionParams = {
      lis_result_sourcedid: 'modelstudent-assignment1',
    };

    const wrapper = renderLtiLaunchApp();
    await waitFor(() => fakeApiCall.called);

    assert.calledWith(fakeApiCall, {
      authToken: 'dummyAuthToken',
      path: '/api/lti/submissions',
      data: fakeConfig.submissionParams,
    });

    // After the successful API call, the iframe should still be rendered.
    wrapper.update();
    assert.isTrue(wrapper.exists('iframe'));
  });

  it('displays an error if reporting the submission fails', async () => {
    fakeConfig.submissionParams = {
      lis_result_sourcedid: 'modelstudent-assignment1',
    };
    const error = new ApiError(400, {});
    fakeApiCall.rejects(error);

    // Wait for the API call to fail and check that an error is displayed.
    const wrapper = renderLtiLaunchApp();
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

  it('does not report a submission if teacher launches assignment', async () => {
    // When a teacher launches the assignment, there will typically be no
    // `submissionParams` config provided by the backend.
    fakeConfig.submissionParams = undefined;

    renderLtiLaunchApp();
    await new Promise(resolve => setTimeout(resolve, 0));

    assert.notCalled(fakeApiCall);
  });

  context('when lmsGrader mode flag is true', () => {
    beforeEach(() => {
      fakeConfig.lmsGrader = true;
      fakeConfig.grading = {
        students: [{ userid: 'user1' }, { userid: 'user2' }],
      };
    });

    it('renders the LMSGrader component', () => {
      const wrapper = renderLtiLaunchApp();
      const LMSGrader = wrapper.find('LMSGrader');
      assert.isTrue(LMSGrader.exists());
    });

    it('creates an iframe key equal to the focused userid', () => {
      const wrapper = renderLtiLaunchApp();
      act(() => {
        wrapper
          .find('LMSGrader')
          .props()
          .onChangeSelectedUser('new_key');
      });
      wrapper.update();
      assert.equal(wrapper.find('iframe').key(), 'new_key');
    });
  });
});
