import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import RelativeTime, { $imports } from '../RelativeTime';

describe('RelativeTime', () => {
  let clock;
  let fakeFormatDateTime;
  let fakeFormatRelativeDate;
  let fakeDecayingInterval;
  const dateTime = '2015-05-10T20:18:56.613388+00:00';

  beforeEach(() => {
    clock = sinon.useFakeTimers();

    fakeFormatDateTime = sinon.stub().returns('absolute date');
    fakeFormatRelativeDate = sinon.stub().returns('relative date');
    fakeDecayingInterval = sinon.stub();

    $imports.$mock({
      '@hypothesis/frontend-shared': {
        formatDateTime: fakeFormatDateTime,
        formatRelativeDate: fakeFormatRelativeDate,
        decayingInterval: fakeDecayingInterval,
      },
    });
  });

  afterEach(() => {
    clock.restore();
    $imports.$restore();
  });

  function createComponent() {
    return mount(<RelativeTime dateTime={dateTime} />);
  }

  it('sets initial time values', () => {
    const wrapper = createComponent();
    const time = wrapper.find('time');

    assert.equal(time.prop('title'), 'absolute date');
    assert.equal(time.prop('dateTime'), dateTime);
    assert.equal(wrapper.text(), 'relative date');
  });

  it('is updated after time passes', () => {
    fakeDecayingInterval.callsFake((date, callback) => {
      const id = setTimeout(callback, 10);
      return () => clearTimeout(id);
    });
    const wrapper = createComponent();
    fakeFormatRelativeDate.returns('60 jiffies');

    act(() => {
      clock.tick(1000);
    });
    wrapper.update();

    assert.equal(wrapper.text(), '60 jiffies');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => {
        // Fake timers break axe-core.
        clock.restore();
        return createComponent();
      },
    }),
  );
});
