import {
  checkAccessibility,
  mount,
  waitFor,
} from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import RevealAnnotationsButton, { $imports } from '../RevealAnnotationsButton';

describe('RevealAnnotationsButton', () => {
  let fakeApiCall;
  let fakeConfig;

  const checkpoint = {
    revealed: false,
    revealDate: null,
    revealUrl: '/api/assignments/1/checkpoint/reveal',
  };

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves({
      revealed: true,
      // h returns timezone-aware datetimes with an explicit offset.
      reveal_date: '2026-07-02T10:00:00.622705+00:00',
    });
    fakeConfig = { api: { authToken: 'dummyAuthToken' } };

    // Keep `Button`/`ModalDialog` real so the click-through works; only mock
    // the API call.
    $imports.$mock({
      '../utils/api': { apiCall: fakeApiCall },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const render = (cp = checkpoint) =>
    mount(
      <Config.Provider value={fakeConfig}>
        <RevealAnnotationsButton checkpoint={cp} />
      </Config.Provider>,
    );

  const clickButton = (wrapper, testId) =>
    wrapper.find(`button[data-testid="${testId}"]`).simulate('click');

  it('renders a reveal button when not revealed', () => {
    const wrapper = render();
    assert.isTrue(wrapper.exists('[data-testid="reveal-annotations-button"]'));
    assert.isFalse(wrapper.exists('[data-testid="checkpoint-revealed"]'));
  });

  it('shows the revealed state when already revealed', () => {
    const wrapper = render({
      ...checkpoint,
      revealed: true,
      revealDate: '2026-07-01T10:00:00',
    });
    assert.isTrue(wrapper.exists('[data-testid="checkpoint-revealed"]'));
    assert.isFalse(wrapper.exists('[data-testid="reveal-annotations-button"]'));
  });

  it('formats reveal dates that have an explicit timezone offset', () => {
    // Regression test: h returns timezone-aware datetimes
    // ("2026-07-01T10:00:00+00:00"). Blindly appending "Z" produced an
    // invalid date and `formatDateTime` threw, freezing the whole app.
    const wrapper = render({
      ...checkpoint,
      revealed: true,
      revealDate: '2026-07-01T10:00:00.622705+00:00',
    });

    const banner = wrapper.find('[data-testid="checkpoint-revealed"]');
    assert.isTrue(banner.exists());
    assert.notInclude(banner.text(), 'Invalid');
    // The formatted date should include the year.
    assert.include(banner.text(), '2026');
  });

  it('shows the revealed state without a reveal date', () => {
    const wrapper = render({ ...checkpoint, revealed: true, revealDate: null });
    assert.isTrue(wrapper.exists('[data-testid="checkpoint-revealed"]'));
  });

  it('opens a confirmation modal when the reveal button is clicked', () => {
    const wrapper = render();
    clickButton(wrapper, 'reveal-annotations-button');
    assert.isTrue(wrapper.exists('ModalDialog'));
  });

  it('closes the modal without revealing when dismissed', () => {
    const wrapper = render();
    clickButton(wrapper, 'reveal-annotations-button');

    act(() => {
      wrapper.find('ModalDialog').prop('onClose')();
    });
    wrapper.update();

    assert.isFalse(wrapper.exists('ModalDialog'));
    assert.notCalled(fakeApiCall);
  });

  it('reveals annotations when confirmed', async () => {
    const wrapper = render();
    clickButton(wrapper, 'reveal-annotations-button');
    clickButton(wrapper, 'confirm-reveal-button');

    await waitFor(() => {
      wrapper.update();
      return wrapper.exists('[data-testid="checkpoint-revealed"]');
    });

    assert.calledWith(fakeApiCall, {
      authToken: 'dummyAuthToken',
      path: checkpoint.revealUrl,
      data: {},
    });
  });

  it('stays unrevealed when the backend reports nothing was revealed', async () => {
    // h is the source of truth. A 200 response doesn't mean a checkpoint was
    // revealed -- if h revealed nothing, the toolbar must not claim otherwise.
    fakeApiCall.resolves({ revealed: false, reveal_date: null });
    const wrapper = render();
    clickButton(wrapper, 'reveal-annotations-button');
    clickButton(wrapper, 'confirm-reveal-button');

    await waitFor(() => {
      wrapper.update();
      return !wrapper.exists('[data-testid="confirm-reveal-button"]');
    });

    assert.isFalse(wrapper.exists('[data-testid="checkpoint-revealed"]'));
    assert.isTrue(wrapper.exists('[data-testid="reveal-annotations-button"]'));
  });

  it('shows an error and keeps the modal open if revealing fails', async () => {
    fakeApiCall.rejects(new Error('boom'));
    const wrapper = render();
    clickButton(wrapper, 'reveal-annotations-button');
    clickButton(wrapper, 'confirm-reveal-button');

    await waitFor(() => {
      wrapper.update();
      return wrapper.exists('ErrorDisplay');
    });

    assert.isFalse(wrapper.exists('[data-testid="checkpoint-revealed"]'));
    assert.isTrue(wrapper.exists('[data-testid="confirm-reveal-button"]'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => render(),
    }),
  );
});
