import { mount } from 'enzyme';

import ErrorModal, { $imports } from '../ErrorModal';
import mockImportedComponents from '../../../test-util/mock-imported-components';

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

    assert.equal(wrapper.find('Modal').props().title, 'Something went wrong');
  });

  it('renders a close button if cancel callback provided', () => {
    const onCancel = sinon.stub();
    const wrapper = createComponent({ onCancel });

    const cancelButton = wrapper.find('LabeledButton');
    assert.equal(cancelButton.text(), 'Close');
    cancelButton.props().onClick();
    assert.calledOnce(onCancel);
  });

  it('Passes title and cancelLabel on to Modal', () => {
    const wrapper = createComponent({
      title: 'My custom title',
      onCancel: sinon.stub(),
      cancelLabel: 'Abort!',
    });

    const modalProps = wrapper.find('Modal').props();
    assert.equal(modalProps.cancelLabel, 'Abort!');
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

      const retryButton = wrapper.find(
        'LabeledButton[data-testid="retry-button"]'
      );
      assert.equal(retryButton.text(), 'Try again');
      assert.equal(retryButton.props().onClick, onRetry);
    });

    it('renders custom labels for retry button', () => {
      const onRetry = sinon.stub();
      const wrapper = createComponent({ onRetry, retryLabel: 'Do-over' });

      const retryButton = wrapper.find(
        'LabeledButton[data-testid="retry-button"]'
      );
      assert.equal(retryButton.text(), 'Do-over');
    });

    it('disables retry button if busy', () => {
      const onRetry = sinon.stub();
      const wrapper = createComponent({ busy: true, onRetry });

      const retryButton = wrapper.find('LabeledButton[variant="primary"]');
      assert.isTrue(retryButton.props().disabled);
    });
  });
});
