import { FileCodeIcon, formatDateTime } from '@hypothesis/frontend-shared';
import { mount } from 'enzyme';

import LastSyncIndicator from '../LastSyncIndicator';

describe('LastSyncIndicator', () => {
  function createComponent(dateTime) {
    return mount(
      <LastSyncIndicator
        icon={FileCodeIcon}
        taskName="task"
        dateTime={dateTime}
      />,
    ).find('[data-testid="container"]');
  }

  [
    { dateTime: null, expectedTitle: undefined },
    {
      dateTime: '2024-10-02T14:24:15.677924+00:00',
      expectedTitle: `task last synced on ${formatDateTime('2024-10-02T14:24:15.677924+00:00', { includeWeekday: true })}`,
    },
  ].forEach(({ dateTime, expectedTitle }) => {
    it('has title when dateTime is not null', () => {
      const wrapper = createComponent(dateTime);
      assert.equal(wrapper.prop('title'), expectedTitle);
    });

    it('shows syncing message when date time is null', () => {
      const wrapper = createComponent(dateTime);
      assert.equal(wrapper.exists('[data-testid="syncing"]'), !dateTime);
    });

    it('shows relative time when dateTime is not null', () => {
      const wrapper = createComponent(dateTime);
      assert.equal(wrapper.exists('RelativeTime'), !!dateTime);
    });
  });
});
