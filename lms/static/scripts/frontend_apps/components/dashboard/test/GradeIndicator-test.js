import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import GradeIndicator from '../GradeIndicator';

describe('GradeIndicator', () => {
  const defaultConfig = {
    grading_type: 'all_or_nothing',
    activity_calculation: 'separate',
    required_annotations: 1,
    required_replies: 1,
  };

  function createComponent({ config = defaultConfig, lastGrade } = {}) {
    return mount(
      <GradeIndicator
        grade={80}
        lastGrade={lastGrade}
        annotations={5}
        replies={2}
        config={config}
      />,
    );
  }

  function getToggleButton(wrapper) {
    return wrapper.find('[data-testid="popover-toggle"]');
  }

  /**
   * @param {'onMouseOver' | 'onMouseOut' | 'onFocus' | 'onBlur'} callback
   */
  function invokeCallback(wrapper, callback) {
    act(() => getToggleButton(wrapper).prop(callback)());
    wrapper.update();
  }

  function openPopover(wrapper) {
    invokeCallback(wrapper, 'onMouseOver');
  }

  function isPopoverVisible(wrapper) {
    return wrapper.exists('[data-testid="popover"]');
  }

  ['onMouseOver', 'onFocus', 'onClick'].forEach(callback => {
    it(`shows popover ${callback}`, () => {
      const wrapper = createComponent();

      assert.isFalse(isPopoverVisible(wrapper));
      invokeCallback(wrapper, callback);
      assert.isTrue(isPopoverVisible(wrapper));
    });
  });

  ['onMouseOut', 'onBlur'].forEach(callback => {
    it(`hides popover ${callback}`, () => {
      const wrapper = createComponent();

      // Start with the popover open
      openPopover(wrapper);
      assert.isTrue(isPopoverVisible(wrapper));

      invokeCallback(wrapper, callback);
      assert.isFalse(isPopoverVisible(wrapper));
    });
  });

  it(`hides popover on Escape key press`, () => {
    const wrapper = createComponent();

    // Start with the popover open
    openPopover(wrapper);
    assert.isTrue(isPopoverVisible(wrapper));

    act(() =>
      document.body.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Escape' }),
      ),
    );
    wrapper.update();

    assert.isFalse(isPopoverVisible(wrapper));
  });

  [
    {
      config: {
        activity_calculation: 'cumulative',
      },
      expectedAnnotationCounts: [
        {
          text: 'Annotations and replies7/2',
          icon: 'CheckIcon',
        },
      ],
    },
    {
      config: {
        activity_calculation: 'cumulative',
        required_annotations: 30,
        required_replies: 5,
      },
      expectedAnnotationCounts: [
        {
          text: 'Annotations and replies7/35',
          icon: 'CancelIcon',
        },
      ],
    },
    {
      config: {
        activity_calculation: 'separate',
        required_annotations: 8,
        required_replies: 15,
      },
      expectedAnnotationCounts: [
        {
          text: 'Annotations5/8',
          icon: 'CancelIcon',
        },
        {
          text: 'Replies2/15',
          icon: 'CancelIcon',
        },
      ],
    },
    {
      config: {
        activity_calculation: 'separate',
      },
      expectedAnnotationCounts: [
        {
          text: 'Annotations5/1',
          icon: 'CheckIcon',
        },
        {
          text: 'Replies2/1',
          icon: 'CheckIcon',
        },
      ],
    },
  ].forEach(({ config, expectedAnnotationCounts }) => {
    it('shows expected annotation counts for config', () => {
      const wrapper = createComponent({
        config: {
          ...defaultConfig,
          ...config,
        },
      });
      openPopover(wrapper);

      const annotationCountElements = wrapper.find('AnnotationCount');
      assert.equal(
        annotationCountElements.length,
        expectedAnnotationCounts.length,
      );

      expectedAnnotationCounts.forEach((expectedAnnotationCount, index) => {
        const annotationCountElement = annotationCountElements.at(index);

        assert.equal(
          annotationCountElement.text(),
          expectedAnnotationCount.text,
        );
        assert.isTrue(
          annotationCountElement.exists(expectedAnnotationCount.icon),
        );
      });
    });
  });

  [true, false].forEach(popoverVisible => {
    it('sets proper aria attributes', () => {
      const wrapper = createComponent();
      if (popoverVisible) {
        openPopover(wrapper);
      }

      const toggleButton = getToggleButton(wrapper);

      assert.equal(toggleButton.prop('aria-expanded'), popoverVisible);
      assert.equal(!!toggleButton.prop('aria-describedby'), popoverVisible);
      assert.equal(!!toggleButton.prop('aria-controls'), popoverVisible);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'popover closed',
        content: () => createComponent(),
      },
      {
        name: 'popover open',
        content: () => {
          const wrapper = createComponent();
          openPopover(wrapper);
          return wrapper;
        },
      },
    ]),
  );

  [
    {
      lastGrade: undefined,
      shouldShowLabel: true,
      shouldShowPrevGrade: false,
    },
    { lastGrade: 90, shouldShowLabel: true, shouldShowPrevGrade: true },
    { lastGrade: 80, shouldShowLabel: false, shouldShowPrevGrade: false },
  ].forEach(({ lastGrade, shouldShowLabel, shouldShowPrevGrade }) => {
    it('shows the "new" label if last grade is not set or is different than current grade', () => {
      const wrapper = createComponent({ lastGrade });
      assert.equal(
        wrapper.exists('[data-testid="new-label"]'),
        shouldShowLabel,
      );
    });

    it('shows last grade in popover if set and is different than current grade', () => {
      const wrapper = createComponent({ lastGrade });
      openPopover(wrapper);
      assert.equal(
        wrapper.exists('[data-testid="last-grade"]'),
        shouldShowPrevGrade,
      );
    });
  });
});
