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

  function createComponent(config = defaultConfig) {
    return mount(
      <GradeIndicator
        grade={100}
        annotations={5}
        replies={2}
        config={config}
      />,
    );
  }

  /**
   * @param {'onMouseOver' | 'onMouseOut' | 'onFocus' | 'onBlur'} callback
   */
  function invokeCallback(wrapper, callback) {
    act(() => wrapper.find('[data-testid="container"]').prop(callback)());
    wrapper.update();
  }

  function openPopover(wrapper) {
    invokeCallback(wrapper, 'onMouseOver');
  }

  function isPopoverVisible(wrapper) {
    return wrapper.exists('[data-testid="popover"]');
  }

  ['onMouseOver', 'onFocus'].forEach(callback => {
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
        ...defaultConfig,
        ...config,
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
});