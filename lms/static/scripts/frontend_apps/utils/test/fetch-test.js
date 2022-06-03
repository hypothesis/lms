import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { useFetch } from '../fetch';
import { delay } from '../../../test-util/wait';

describe('useFetch', () => {
  let wrappers;

  function TestWidget({ fetchKey, fetcher }) {
    const thing = useFetch(fetchKey, fetcher);

    // This could be simplified to `isIdle = fetchKey === null`, but we want
    // to check the `useFetch` result matches expectations in the idle case.
    const isIdle = !thing.data && !thing.error && !thing.isLoading;

    return (
      <div>
        {isIdle && 'Nothing to fetch'}
        {thing.isLoading && 'Loading'}
        {thing.error && `Error: ${thing.error.message}`}
        {thing.data && `Data: ${thing.data}`}
      </div>
    );
  }

  function renderWidget(key, fetcher) {
    const widget = mount(<TestWidget fetchKey={key} fetcher={fetcher} />);
    wrappers.push(widget);
    return widget;
  }

  async function waitForFetch(wrapper) {
    await act(() => delay(0));
    wrapper.update();
  }

  beforeEach(() => {
    wrappers = [];
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
  });

  it('returns loading state initially if loading', () => {
    const wrapper = renderWidget('some-key', async () => 'Some data');
    assert.equal(wrapper.text(), 'Loading');
  });

  [async () => 'Some data', undefined, null].forEach(fetcher => {
    it('returns idle state if not loading', () => {
      const wrapper = renderWidget(null, fetcher);
      assert.equal(wrapper.text(), 'Nothing to fetch');
    });
  });

  it('fetches data and returns result', async () => {
    const wrapper = renderWidget('some-key', async () => 'Some data');
    await waitForFetch(wrapper);
    assert.equal(wrapper.text(), 'Data: Some data');
  });

  it('cancels fetch if key changes', () => {
    let signal;
    const wrapper = renderWidget('some-key', async signal_ => {
      signal = signal_;
      return 'Some data';
    });

    wrapper.setProps({
      key: 'other-key',
      fetcher: async () => 'Different data',
    });

    assert.isTrue(signal.aborted);
  });

  it('returns error if fetch fails', async () => {
    const wrapper = renderWidget('some-key', async () => {
      throw new Error('Some error');
    });
    await waitForFetch(wrapper);
    assert.equal(wrapper.text(), 'Error: Some error');
  });

  it('transitions to loading state if key changes', async () => {
    const wrapper = renderWidget('some-key', async () => 'Some data');
    await waitForFetch(wrapper);
    assert.equal(wrapper.text(), 'Data: Some data');

    wrapper.setProps({
      fetchKey: 'other-key',
      fetcher: async () => 'Different data',
    });
    assert.equal(wrapper.text(), 'Loading');

    await waitForFetch(wrapper);
    assert.equal(wrapper.text(), 'Data: Different data');
  });

  it('transitions to idle state if key is set to null', async () => {
    const wrapper = renderWidget('some-key', async () => 'Some data');
    await waitForFetch(wrapper);
    assert.equal(wrapper.text(), 'Data: Some data');

    wrapper.setProps({ fetchKey: null });

    assert.equal(wrapper.text(), 'Nothing to fetch');
  });

  it('cancels fetch if component is unmounted', () => {
    let signal;
    const wrapper = renderWidget('some-key', async signal_ => {
      signal = signal_;
      return 'Some data';
    });

    wrapper.unmount();

    assert.isTrue(signal.aborted);
  });

  it('throws if a key is set but a fetcher is not', () => {
    assert.throws(() => {
      renderWidget('some-key');
    }, 'Fetch key provided but no fetcher set');
  });
});
