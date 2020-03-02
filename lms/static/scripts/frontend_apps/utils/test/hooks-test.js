import { useUniqueId } from '../hooks';

describe('hooks', () => {
  it('generates unique ids each time useUniqueId is called', () => {
    const id1 = useUniqueId('prefix:');
    const id2 = useUniqueId('prefix:');
    assert.notEqual(id1, id2);
  });
});
