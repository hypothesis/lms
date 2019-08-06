import { createElement } from 'preact';
import { mount } from 'enzyme';

import { Config } from '../../config';
import { ApiError } from '../../utils/api';

import BasicLtiLaunchApp, { $imports } from '../BasicLtiLaunchApp';

/**
 * Return a Promise that resolves on the next turn of the event loop.
 *
 * This gives any pending async microtasks a chance to execute.
 * See https://jakearchibald.com/2015/tasks-microtasks-queues-and-schedules/.
 */
function nextTick() {
  return new Promise(resolve => setTimeout(resolve));
}

describe('BasicLtiLaunchApp', () => {
  let fakeApiCall;
  let FakeAuthWindow;
  let fakeConfig;

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

    const FakeErrorDisplay = () => null;
    const FakeSpinner = () => null;

    // nb. We mock components manually rather than using Enzyme's
    // shallow rendering because the modern context API doesn't seem to work
    // with shallow rendering yet
    $imports.$mock({
      './ErrorDisplay': FakeErrorDisplay,
      './Spinner': FakeSpinner,

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

      await nextTick();

      assert.calledWith(fakeApiCall, {
        authToken: 'dummyAuthToken',
        path: 'https://lms.hypothes.is/api/files/1234',
      });
      assert.isTrue(wrapper.exists('FakeSpinner'));
    });

    it('displays the content URL in an iframe if successfully fetched', async () => {
      fakeApiCall.resolves({
        via_url: 'https://via.hypothes.is/123',
      });

      const wrapper = renderLtiLaunchApp();

      await nextTick();
      wrapper.update();

      const iframe = wrapper.find('iframe');
      assert.isTrue(iframe.exists());
      assert.include(iframe.props(), {
        src: 'https://via.hypothes.is/123',
      });
    });

    it('displays authorization prompt if content URL fetch fails with an `ApiError`', async () => {
      // Make the initial URL fetch request reject with an unspecified `ApiError`.
      fakeApiCall.rejects(new ApiError(400, {}));

      const wrapper = renderLtiLaunchApp();
      await nextTick();

      // Verify that an "Authorize" prompt is shown.
      wrapper.update();
      const authButton = wrapper.find('Button[label="Authorize"]');
      assert.isTrue(authButton.exists());

      // Click the "Authorize" button and verify that authorization is attempted.
      fakeApiCall.reset();
      fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
      authButton.prop('onClick')();
      assert.called(FakeAuthWindow);

      // Check that files are fetched after authorization completes.
      await new Promise(resolve => {
        setTimeout(resolve, 0);
      });
      wrapper.update();

      assert.equal(
        wrapper.find('iframe').prop('src'),
        'https://via.hypothes.is/123'
      );
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
        await nextTick();

        // Verify that a "Try again" prompt is shown.
        wrapper.update();
        const tryAgainButton = wrapper.find('Button[label="Try again"]');
        assert.isTrue(tryAgainButton.exists());

        // Click the "Try again" button and verify that authorization is attempted.
        fakeApiCall.reset();
        fakeApiCall.resolves({ via_url: 'https://via.hypothes.is/123' });
        tryAgainButton.prop('onClick')();
        assert.called(FakeAuthWindow);

        // Check that files are fetched after authorization completes.
        await nextTick();
        wrapper.update();
        assert.equal(
          wrapper.find('iframe').prop('src'),
          'https://via.hypothes.is/123'
        );
      });
    });
  });
});
