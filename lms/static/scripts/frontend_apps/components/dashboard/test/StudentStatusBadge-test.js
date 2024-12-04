import { mount } from 'enzyme';

import StudentStatusBadge from '../StudentStatusBadge';

describe('StudentStatusBadge', () => {
  [
    { type: 'new', expectedText: 'New' },
    { type: 'error', expectedText: 'Error' },
    { type: 'syncing', expectedText: 'Syncing' },
    { type: 'drop', expectedText: 'Drop' },
  ].forEach(({ type, expectedText }) => {
    it('shows right text based on type', () => {
      const badge = mount(<StudentStatusBadge type={type} />);
      assert.equal(badge.text(), expectedText);
    });
  });
});
