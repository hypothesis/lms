import { waitForElement } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
import { useState } from 'preact/hooks';

import DataLoader from '../DataLoader';

async function fetchMessage() {
  return 'Example message';
}

function TestContent({ message }) {
  return <div data-testid="content">{message}</div>;
}

function TestContainer({ initialMessage = null, load = fetchMessage }) {
  const [message, setMessage] = useState(initialMessage);

  return (
    <div>
      <DataLoader loaded={message !== null} load={load} onLoad={setMessage}>
        <TestContent message={message} />
      </DataLoader>
    </div>
  );
}

describe('DataLoader', () => {
  it('renders content if loaded', () => {
    const wrapper = mount(<TestContainer initialMessage="Test" />);
    const content = wrapper.find('[data-testid="content"]');
    assert.isTrue(content.exists());
    assert.equal(content.text(), 'Test');
  });

  it('loads content if not already loaded', async () => {
    const load = sinon.spy(async () => 'Hello world');
    const wrapper = mount(<TestContainer load={load} />);

    assert.isTrue(wrapper.exists('SpinnerOverlay'));
    assert.calledOnce(load);

    const content = await waitForElement(wrapper, '[data-testid="content"]');
    assert.equal(content.text(), 'Hello world');
    assert.isFalse(wrapper.exists('SpinnerOverlay'));
  });

  it('renders error if content failed to load', async () => {
    const error = new Error('Request failed');
    const load = sinon.spy(async () => {
      throw error;
    });
    const wrapper = mount(<TestContainer load={load} />);

    assert.isTrue(wrapper.exists('SpinnerOverlay'));
    assert.calledOnce(load);

    const errorDisplay = await waitForElement(wrapper, 'ErrorModal');
    assert.equal(errorDisplay.prop('error'), error);
    assert.isFalse(wrapper.exists('[data-testid="content"]'));
    assert.isFalse(wrapper.exists('SpinnerOverlay'));
  });

  it('aborts loading when DataLoader is unmounted', () => {
    const onAbort = sinon.stub();
    const wrapper = mount(
      <TestContainer
        load={async signal => {
          signal.onabort = onAbort;
          return 'Hello world';
        }}
      />,
    );

    wrapper.unmount();
    assert.called(onAbort);
  });
});
