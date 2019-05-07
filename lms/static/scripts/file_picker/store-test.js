import Store from './store';

class Subscriber {
  handleUpdate() {}
}

describe('store', () => {
  beforeEach(() => {
    window.DEFAULT_SETTINGS = {};
  });

  it('#subscribe should correctly subscribe observers', () => {
    const store = new Store();
    const sub = new Subscriber();
    store.subscribe(sub);
    assert.equal(store.subscribers.length, 1);
  });

  it('#triggerUpdate should call the subscribers handleUpdateMethod', () => {
    const store = new Store();
    const sub = new Subscriber();
    sub.handleUpdate = sinon.stub();
    store.subscribe(sub);
    store.triggerUpdate('TEST_UPDATE');
    assert.calledWith(sub.handleUpdate, store.getState(), 'TEST_UPDATE');
  });

  it('#setState should change the state value and call trigger update', () => {
    const store = new Store();
    const sub = new Subscriber();
    store.triggerUpdate = sinon.stub();
    const newState = {};
    store.subscribe(sub);
    store.setState(newState, 'TEST_UPDATE');
    assert.equal(store.getState(), newState);
    assert.calledWith(store.triggerUpdate, 'TEST_UPDATE');
  });

  it('#unsubscribe should unsubscribe', () => {
    const sub = new Subscriber();
    const store = new Store([sub]);
    store.unsubscribe(sub);
    assert.equal(store.subscribers.length, 0);
  });
});
