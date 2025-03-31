import { mount } from '@hypothesis/frontend-testing';

import EmailMentionsPreferences from '../EmailMentionsPreferences';

describe('EmailMentionsPreferences', () => {
  function createComponent(subscribed) {
    return mount(<EmailMentionsPreferences subscribed={subscribed} />);
  }

  [true, false].forEach(subscribed => {
    it('sets defaultChecked in checkbox based on subscription status', () => {
      const wrapper = createComponent(subscribed);
      assert.equal(
        wrapper
          .find('Checkbox[data-testid="mentions-checkbox"]')
          .prop('defaultChecked'),
        subscribed,
      );
    });
  });
});
