import { render } from 'preact';

import { useUniqueId } from '../hooks';

describe('hooks', () => {
  it('generates unique ids each time useUniqueId is called', () => {
    let id1;
    let id2;

    function Widget() {
      id1 = useUniqueId('prefix:');
      id2 = useUniqueId('prefix:');
      return null;
    }
    render(<Widget />, document.createElement('div'));

    assert.typeOf(id1, 'string');
    assert.typeOf(id2, 'string');
    assert.isTrue(id1.startsWith('prefix:'));
    assert.isTrue(id2.startsWith('prefix:'));
    assert.notEqual(id1, id2);
  });
});
