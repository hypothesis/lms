import { mount } from 'enzyme';
import { useState } from 'preact/hooks';

import { useWarnOnPageUnload } from '../use-warn-on-page-unload';

describe('useWarnOnPageUnload', () => {
  let fakeWindow;
  const FakeComponent = () => {
    const [isUnsaved, setUnsaved] = useState(true);

    useWarnOnPageUnload(isUnsaved, fakeWindow);

    return (
      <button type="button" onClick={() => setUnsaved(false)}>
        Set not unsaved
      </button>
    );
  };
  const createComponent = () => mount(<FakeComponent />);

  const waitForBeforeUnloadEvent = () => {
    const promise = new Promise(resolve =>
      fakeWindow.addEventListener('beforeunload', resolve),
    );
    fakeWindow.dispatchEvent(new Event('beforeunload', { cancelable: true }));

    return promise;
  };

  beforeEach(() => {
    fakeWindow = new EventTarget();
  });

  it('registers event listener when unsaved data is true', async () => {
    createComponent();

    const event = await waitForBeforeUnloadEvent();

    assert.isTrue(event.defaultPrevented);
    assert.equal(event.returnValue, '');
  });

  it('unregisters event listener when unsaved data is false', async () => {
    const wrapper = createComponent();

    wrapper.find('button').simulate('click');
    wrapper.update();

    const event = await waitForBeforeUnloadEvent();

    assert.isFalse(event.defaultPrevented);
  });

  it('unregisters event listener when component is unmounted', async () => {
    const wrapper = createComponent();
    wrapper.unmount();

    const event = await waitForBeforeUnloadEvent();

    assert.isFalse(event.defaultPrevented);
  });
});
