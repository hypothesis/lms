import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import ContentWithBadge from '../ContentWithBadge';

describe('ContentWithBadge', () => {
  function createComponent(props) {
    return mount(<ContentWithBadge {...props} />);
  }

  [
    { count: 15, hasMoreItems: false, expectedValue: '15' },
    { count: 581, hasMoreItems: false, expectedValue: '581' },
    { count: 200, hasMoreItems: true, expectedValue: '200+' },
    { count: 100, hasMoreItems: true, expectedValue: '99+' },
    { count: 1000, hasMoreItems: true, expectedValue: '1000+' },
  ].forEach(({ expectedValue, hasMoreItems, count }) => {
    it('displays expected value in count badge', () => {
      const wrapper = createComponent({ count, hasMoreItems });
      const badge = wrapper.find('[data-testid="count-badge"]');

      assert.equal(badge.text(), expectedValue);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent({ count: 10 }),
    }),
  );
});
