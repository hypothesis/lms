import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import ErrorModal, { $imports } from '../ErrorModal';

describe('ErrorModal', () => {
  let fakeError;

  const createComponent = (props = {}) =>
    mount(<ErrorModal description="Oh no!" error={fakeError} {...props} />);

  beforeEach(() => {
    fakeError = new Error('It broke');
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('displays details of the error with a default title', () => {
    const wrapper = createComponent();

    assert.include(wrapper.find('ErrorDisplay').props(), {
      description: 'Oh no!',
      error: fakeError,
    });

    assert.equal(
      wrapper.find('ModalDialog').props().title,
      'Something went wrong',
    );
  });

  it('renders a close button if cancel callback provided', () => {
    const onCancel = sinon.stub();
    const wrapper = createComponent({ onCancel });

    const cancelButton = wrapper.find('button[data-testid="cancel-button"]');
    assert.equal(cancelButton.text(), 'Close');
    cancelButton.props().onClick();
    assert.calledOnce(onCancel);
  });

  it('renders a custom label on close button if provided', () => {
    const onCancel = sinon.stub();
    const wrapper = createComponent({ onCancel, cancelLabel: 'Oh no!' });

    const cancelButton = wrapper.find('button[data-testid="cancel-button"]');
    assert.equal(cancelButton.text(), 'Oh no!');
  });

  it('renders extra actions if provided', () => {
    const extraActions = (
      <>
        <button data-testid="button-a">Click me</button>
        <button data-testid="button-b">No, pick me!</button>
      </>
    );

    const wrapper = createComponent({ extraActions });

    assert.isTrue(wrapper.exists('[data-testid="button-a"]'));
    assert.isTrue(wrapper.exists('[data-testid="button-b"]'));
  });

  it('Passes title on to Modal', () => {
    const wrapper = createComponent({
      title: 'My custom title',
    });

    const modalProps = wrapper.find('ModalDialog').props();
    assert.equal(modalProps.title, 'My custom title');
  });

  it('does not render error details if no error is provided', () => {
    const wrapper = mount(<ErrorModal>My error</ErrorModal>);
    assert.isFalse(wrapper.find('ErrorDisplay').exists());
  });

  describe('retry button', () => {
    it('renders a retry button if a retry callback is provided', () => {
      const onRetry = sinon.stub();
      const wrapper = createComponent({ onRetry });

      const retryButton = wrapper.find('button[data-testid="retry-button"]');
      assert.equal(retryButton.text(), 'Try again');
      assert.equal(retryButton.props().onClick, onRetry);
    });

    it('renders custom labels for retry button', () => {
      const onRetry = sinon.stub();
      const wrapper = createComponent({ onRetry, retryLabel: 'Do-over' });

      const retryButton = wrapper.find('button[data-testid="retry-button"]');
      assert.equal(retryButton.text(), 'Do-over');
    });

    it('disables retry button if busy', () => {
      const onRetry = sinon.stub();
      const wrapper = createComponent({ busy: true, onRetry });

      const retryButton = wrapper.find('button[data-testid="retry-button"]');
      assert.isTrue(retryButton.props().disabled);
    });
  });
});
