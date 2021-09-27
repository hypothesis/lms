import { mount } from 'enzyme';

import { Config } from '../../config';

import OAuth2RedirectErrorApp from '../OAuth2RedirectErrorApp';

describe('OAuth2RedirectErrorApp', () => {
  let fakeConfig;
  let fakeLocation;

  const renderApp = () => {
    const config = {
      OAuth2RedirectError: fakeConfig,
    };

    return mount(
      <Config.Provider value={config}>
        <OAuth2RedirectErrorApp location={fakeLocation} />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      authUrl: null,
      canvasScopes: [],
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
    fakeConfig.errorCode = 'canvas_invalid_scope';
    fakeConfig.canvasScopes = ['scope_a', 'scope_b'];

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      "A Canvas admin needs to edit Hypothesis's developer key"
    );
    fakeConfig.canvasScopes.forEach(scope =>
      assert.include(wrapper.text(), scope)
    );
  });

  it('shows a different title and description for blackboard_missing_integration', () => {
    fakeConfig.errorCode = 'blackboard_missing_integration';
    const wrapper = renderApp();
    assert.include(wrapper.text(), 'Missing Blackboard REST API integration');
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
      description: 'Something went wrong when authorizing Hypothesis',
    });
    assert.deepEqual(errorDisplay.prop('error'), {
      details: fakeConfig.errorDetails,
      code: null,
    });
  });

  it(`closes the window when the dialog's "Close" button is clicked`, () => {
    const wrapper = renderApp();
    wrapper.find('LabeledButton[data-testid="close"]').props().onClick();
    assert.called(window.close);
  });

  it('shows "Try again" button if retry URL is provided', () => {
    const initialLocation = fakeLocation.href;
    fakeConfig.authUrl = 'https://lms.hypothes.is/auth/url';

    const wrapper = renderApp();
    const tryAgainButton = wrapper.find(
      'LabeledButton[data-testid="try-again"]'
    );
    assert.isTrue(tryAgainButton.exists());
    assert.equal(fakeLocation.href, initialLocation);

    tryAgainButton.props().onClick();

    assert.equal(fakeLocation.href, fakeConfig.authUrl);
  });

  it('does not show "Try again" button if no retry URL is provided', () => {
    const wrapper = renderApp();
    assert.isFalse(wrapper.exists('LabeledButton[data-testid="try-again"]'));
  });
});
