import { mount } from 'enzyme';
import { createElement } from 'preact';

import { Config } from '../../config';

import CanvasOAuth2RedirectErrorApp from '../CanvasOAuth2RedirectErrorApp';

describe('CanvasOAuth2RedirectErrorApp', () => {
  let fakeConfig;
  let fakeLocation;

  const renderApp = () => {
    const config = {
      canvasOAuth2RedirectError: fakeConfig,
    };

    return mount(
      <Config.Provider value={config}>
        <CanvasOAuth2RedirectErrorApp location={fakeLocation} />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      invalidScope: false,
      authorizeUrl: null,
      scopes: [],
    };

    fakeLocation = {
      href: '',
    };

    sinon.stub(window, 'close');
  });

  afterEach(() => {
    window.close.restore();
  });

  it('shows a scope error if the scope is invalid', () => {
    fakeConfig.invalidScope = true;
    fakeConfig.scopes = ['scope_a', 'scope_b'];

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      "A Canvas admin needs to edit Hypothesis's developer key"
    );
    fakeConfig.scopes.forEach(scope => assert.include(wrapper.text(), scope));
  });

  it('shows a generic error if the scope is valid', () => {
    const wrapper = renderApp();
    assert.notInclude(wrapper.text(), 'A Canvas admin needs to edit');
  });

  it('renders error details', () => {
    fakeConfig.errorDetails = 'Technical details';

    const wrapper = renderApp();

    const errorDisplay = wrapper.find('ErrorDisplay');
    assert.include(errorDisplay.props(), {
      message: 'Something went wrong when authorizing Hypothesis',
    });
    assert.deepEqual(errorDisplay.prop('error'), {
      details: fakeConfig.errorDetails,
    });
  });

  it(`closes the window when the dialog's "Cancel" button is clicked`, () => {
    const wrapper = renderApp();
    wrapper.find('Dialog').props().onCancel();
    assert.called(window.close);
  });

  it('shows "Try again" button if retry URL is provided', () => {
    const initialLocation = fakeLocation.href;
    fakeConfig.authorizeUrl = 'https://lms.hypothes.is/auth/url';

    const wrapper = renderApp();
    const tryAgainButton = wrapper.find('Button[label="Try again"]');
    assert.isTrue(tryAgainButton.exists());
    assert.equal(fakeLocation.href, initialLocation);

    tryAgainButton.props().onClick();

    assert.equal(fakeLocation.href, fakeConfig.authorizeUrl);
  });

  it('does not show "Try again" button if no retry URL is provided', () => {
    const wrapper = renderApp();
    assert.isFalse(wrapper.exists('Button[label="Try again"]'));
  });
});
