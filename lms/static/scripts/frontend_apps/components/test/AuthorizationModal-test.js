import { mount } from 'enzyme';

import AuthorizationModal from '../AuthorizationModal';

describe('AuthorizationModal', () => {
  let fakeOnAuthComplete;

  const createComponent = (props = {}) =>
    mount(
      <AuthorizationModal
        authToken="123456"
        authURL="http://https://example.com/authorize"
        onAuthComplete={fakeOnAuthComplete}
        {...props}
      />
    );

  beforeEach(() => {
    fakeOnAuthComplete = sinon.stub();
  });

  it('provides an authorization button', () => {
    const wrapper = createComponent();
    const authorizeButton = wrapper.find('LabeledButton');

    assert.equal(authorizeButton.length, 1);
    assert.equal(authorizeButton.text(), 'Authorize');
  });

  it('displays a cancel button if onCancel provided', () => {
    const onCancel = sinon.stub();
    const wrapper = createComponent({ onCancel });

    const cancelButton = wrapper.find(
      'LabeledButton[data-testid="cancel-button"]'
    );

    assert.equal(cancelButton.text(), 'Cancel');
    assert.equal(cancelButton.props().onClick, onCancel);
  });

  it('sets a default title', () => {
    const wrapper = createComponent();
    const wrappedErrorModal = wrapper.find('ErrorModal');

    assert.equal(wrappedErrorModal.props().title, 'Authorize Hypothesis');
  });
});
