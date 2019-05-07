import Component from './component';
import Store from '../store';

class TestComponent1 extends Component {
  render() {
    return 'Test1';
  }
}

class TestComponent2 extends Component {
  render() {
    return 'Test2';
  }
}

describe('component', () => {
  beforeEach(() => {
    window.DEFAULT_SETTINGS = {};
  });

  it('#r should render single sub components', () => {
    const store = new Store();
    const component = new Component(store);
    const output = component.r`${new TestComponent1(
      store
    )}${new TestComponent2()}`;
    assert.equal(output, 'Test1Test2');
  });

  it('#r should render lists of sub components', () => {
    const store = new Store();
    const component = new Component(store);
    const output = component.r`${[
      new TestComponent1(store),
      new TestComponent2(store),
    ]}`;
    assert.equal(output, 'Test1Test2');
  });

  it('#r should render primative values', () => {
    const store = new Store();
    const component = new Component(store);
    const output = component.r`${'hello world'}`;
    assert.equal(output, 'hello world');
  });
});
