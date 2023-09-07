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

  beforeEach(() => {
    fakeWindow = new EventTarget();
    sinon.spy(fakeWindow, 'addEventListener');
    sinon.spy(fakeWindow, 'removeEventListener');
  });

  it('registers event listener when unsaved data is true', () => {
    createComponent();

    assert.called(fakeWindow.addEventListener);
    assert.notCalled(fakeWindow.removeEventListener);
  });

  it('unregisters event listener when unsaved data is false', () => {
    const wrapper = createComponent();

    wrapper.find('button').simulate('click');
    wrapper.update();

    assert.called(fakeWindow.removeEventListener);
  });

  it('unregisters event listener when component is unmounted', () => {
    const wrapper = createComponent();
    wrapper.unmount();

    assert.called(fakeWindow.removeEventListener);
  });

  it('acts on provided event when listener is invoked', () => {
    createComponent();

    const event = new Event('beforeunload');
    sinon.stub(event, 'preventDefault');

    fakeWindow.dispatchEvent(event);

    assert.called(event.preventDefault);
  });
});
