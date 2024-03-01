import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import AuthButton, { $imports } from '../AuthButton';

describe('AuthButton', () => {
  const authToken = 'dummy-token';
  const authURL = 'https://example.com/authorize';

  let FakeAuthWindow;
  let fakeAuthWindow;

  beforeEach(() => {
    fakeAuthWindow = {
      authorize: sinon.stub().resolves(),
      close: sinon.stub(),
      focus: sinon.stub(),
    };
    FakeAuthWindow = sinon.stub().returns(fakeAuthWindow);

    $imports.$mock({
      '../utils/AuthWindow': FakeAuthWindow,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent(props = {}) {
    const noop = () => {};

    return mount(
      <AuthButton
        authToken={authToken}
        authURL={authURL}
        onAuthComplete={noop}
        {...props}
      />,
    );
  }

  function getButton(wrapper) {
    return wrapper.find('button[data-testid="auth-button"]');
  }

  it('shows authorization popup when button is clicked', () => {
    const wrapper = createComponent();

    act(() => {
      getButton(wrapper).props().onClick();
    });

    assert.calledWith(FakeAuthWindow, { authToken, authUrl: authURL });
    assert.called(fakeAuthWindow.authorize);
  });

  it('focuses the existing popup if open when button is clicked', () => {
    const wrapper = createComponent();

    act(() => {
      getButton(wrapper).props().onClick();
    });
    assert.notCalled(fakeAuthWindow.focus);

    act(() => {
      getButton(wrapper).props().onClick();
    });
    assert.called(fakeAuthWindow.focus);

    // Popup window should not be created a second time.
    assert.calledOnce(FakeAuthWindow);
    assert.calledOnce(fakeAuthWindow.authorize);
  });

  it('invokes `onAuthComplete` callback when authorization completes', () => {
    let onAuthComplete;
    const authCompleteCalled = new Promise(
      resolve => (onAuthComplete = resolve),
    );
    const wrapper = createComponent({ onAuthComplete });

    act(() => {
      getButton(wrapper).props().onClick();
    });

    return authCompleteCalled;
  });

  it('shows custom label', () => {
    const wrapper = createComponent({ label: 'Try again' });
    assert.equal(getButton(wrapper).text(), 'Try again');
  });

  it('closes the authorization popup when unmounted', () => {
    const wrapper = createComponent();

    act(() => {
      getButton(wrapper).props().onClick();
    });
    wrapper.unmount();

    assert.calledOnce(fakeAuthWindow.close);
  });
});
