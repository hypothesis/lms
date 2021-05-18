import { mount } from 'enzyme';
import { createElement } from 'preact';
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
      />
    );
  }

  it('shows authorization popup when button is clicked', () => {
    const authButton = createComponent();

    act(() => {
      authButton.find('LabeledButton').props().onClick();
    });

    assert.calledWith(FakeAuthWindow, { authToken, authUrl: authURL });
    assert.called(fakeAuthWindow.authorize);
  });

  it('focuses the existing popup if open when button is clicked', () => {
    const authButton = createComponent();

    act(() => {
      authButton.find('LabeledButton').props().onClick();
    });
    assert.notCalled(fakeAuthWindow.focus);

    act(() => {
      authButton.find('LabeledButton').props().onClick();
    });
    assert.called(fakeAuthWindow.focus);

    // Popup window should not be created a second time.
    assert.calledOnce(FakeAuthWindow);
    assert.calledOnce(fakeAuthWindow.authorize);
  });

  it('invokes `onAuthComplete` callback when authorization completes', () => {
    let onAuthComplete;
    const authCompleteCalled = new Promise(
      resolve => (onAuthComplete = resolve)
    );
    const authButton = createComponent({ onAuthComplete });

    act(() => {
      authButton.find('LabeledButton').props().onClick();
    });

    return authCompleteCalled;
  });

  it('shows custom label', () => {
    const authButton = createComponent({ label: 'Try again' });
    assert.equal(authButton.find('LabeledButton').text(), 'Try again');
  });

  it('closes the authorization popup when unmounted', () => {
    const authButton = createComponent();

    act(() => {
      authButton.find('LabeledButton').props().onClick();
    });
    authButton.unmount();

    assert.calledOnce(fakeAuthWindow.close);
  });
});
