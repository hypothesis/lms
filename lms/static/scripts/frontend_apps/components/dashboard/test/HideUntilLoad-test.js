import { mount } from 'enzyme';
import { useContext } from 'preact/hooks';

import { InitialLoadingContext } from '../../../utils/initial-loading-context';
import HideUntilLoad from '../../HideUntilLoad';

function ContentComponent() {
  const { startLoading, finishLoading, reportFatalError } = useContext(
    InitialLoadingContext,
  );

  return (
    <div data-testid="children">
      <button data-testid="start-foo" onClick={() => startLoading('foo')}>
        Start foo
      </button>
      <button data-testid="finish-foo" onClick={() => finishLoading('foo')}>
        Finish foo
      </button>
      <button data-testid="start-bar" onClick={() => startLoading('bar')}>
        Start bar
      </button>
      <button data-testid="finish-bar" onClick={() => finishLoading('bar')}>
        Finish bar
      </button>
      <button
        data-testid="fatal-error"
        onClick={() => reportFatalError(new Error('Something went wrong'))}
      >
        Fatal error
      </button>
    </div>
  );
}

describe('HideUntilLoad', () => {
  function createComponent(footer) {
    return mount(
      <HideUntilLoad footer={footer}>
        <ContentComponent />
      </HideUntilLoad>,
    );
  }

  function loadingIndicatorIsVisible(wrapper) {
    return wrapper.exists('[data-testid="initial-load-indicator"]');
  }

  function childrenWrapperIsVisible(wrapper) {
    return !wrapper
      .find('[data-testid="children-wrapper"]')
      .getDOMNode()
      .classList.contains('hidden');
  }

  function errorIsVisible(wrapper) {
    return wrapper.exists('ErrorDisplay');
  }

  function startLoading(wrapper, id) {
    wrapper.find(`[data-testid="start-${id}"]`).simulate('click');
  }

  function finishLoading(wrapper, id) {
    wrapper.find(`[data-testid="finish-${id}"]`).simulate('click');
  }

  function reportFatalError(wrapper) {
    wrapper.find('[data-testid="fatal-error"]').simulate('click');
  }

  it('is in loading state at first', () => {
    const wrapper = createComponent();

    assert.isTrue(loadingIndicatorIsVisible(wrapper));
    assert.isFalse(childrenWrapperIsVisible(wrapper));
  });

  it('removes loading indicator once all individual loadings have finished', () => {
    const wrapper = createComponent();

    // We start two individual loadings
    startLoading(wrapper, 'foo');
    startLoading(wrapper, 'bar');

    // After one of them has finished, we are still showing the loading indicator
    finishLoading(wrapper, 'bar');
    assert.isTrue(loadingIndicatorIsVisible(wrapper));
    assert.isFalse(childrenWrapperIsVisible(wrapper));

    // Once all have finished, we no longer show the loading indicator
    finishLoading(wrapper, 'foo');
    assert.isFalse(loadingIndicatorIsVisible(wrapper));
    assert.isTrue(childrenWrapperIsVisible(wrapper));
  });

  it('no longer shows loading indicator once all initial loadings have finished once', () => {
    const wrapper = createComponent();

    // We start and finish a loading
    startLoading(wrapper, 'foo');
    finishLoading(wrapper, 'foo');

    // Loading indicator is not shown
    assert.isFalse(loadingIndicatorIsVisible(wrapper));
    assert.isTrue(childrenWrapperIsVisible(wrapper));

    // If we start another loading, the loading indicator is still not shown
    startLoading(wrapper, 'bar');
    assert.isFalse(loadingIndicatorIsVisible(wrapper));
    assert.isTrue(childrenWrapperIsVisible(wrapper));
  });

  it('replaces children with error when a fatal error is reported', () => {
    const wrapper = createComponent();

    reportFatalError(wrapper);

    assert.isFalse(loadingIndicatorIsVisible(wrapper));
    assert.isTrue(childrenWrapperIsVisible(wrapper));
    assert.isFalse(wrapper.exists('[data-testid="children"]'));
    assert.isTrue(errorIsVisible(wrapper));
  });

  it('shows footer only when loaded or error', () => {
    const wrapper = createComponent(
      <footer data-testid="footer">The footer</footer>,
    );
    const footerIsVisible = () => wrapper.exists('[data-testid="footer"]');

    // Footer is not visible while loading
    startLoading(wrapper, 'foo');
    assert.isFalse(footerIsVisible());

    // Footer is visible after initial load
    finishLoading(wrapper, 'foo');
    assert.isTrue(footerIsVisible());

    // Footer is still visible after reporting an error
    reportFatalError(wrapper);
    assert.isTrue(footerIsVisible());
  });
});
