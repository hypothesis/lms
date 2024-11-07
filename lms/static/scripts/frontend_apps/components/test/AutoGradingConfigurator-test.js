import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import AutoGradingConfigurator from '../AutoGradingConfigurator';

describe('AutoGradingConfigurator', () => {
  let fakeAutoGradingConfig;
  let fakeUpdateAutoGradingConfig;

  beforeEach(() => {
    fakeAutoGradingConfig = {
      grading_type: 'scaled',
      activity_calculation: 'cumulative',
      required_annotations: 1,
    };
    fakeUpdateAutoGradingConfig = sinon.stub();
  });

  function createComponent() {
    return mount(
      <AutoGradingConfigurator
        config={fakeAutoGradingConfig}
        onChange={fakeUpdateAutoGradingConfig}
      />,
    );
  }

  function dispatchOnChange(wrapper, selector, event) {
    act(() => wrapper.find(selector).props().onChange(event));
  }

  [true, false].forEach(enabled => {
    it('renders components if auto grading is enabled', () => {
      fakeAutoGradingConfig.enabled = enabled;
      const wrapper = createComponent();

      assert.equal(wrapper.exists('RadioGroup'), enabled);
    });

    it('updates config when checkbox is changed', () => {
      const wrapper = createComponent();

      dispatchOnChange(wrapper, 'Checkbox', {
        target: { checked: enabled },
      });

      assert.calledWith(fakeUpdateAutoGradingConfig, sinon.match({ enabled }));
    });
  });

  context('when auto grading is enabled', () => {
    beforeEach(() => {
      fakeAutoGradingConfig.enabled = true;
    });

    ['cumulative', 'separate'].forEach(activityCalculation => {
      it('updates config when changing activity calculation', () => {
        const wrapper = createComponent();

        dispatchOnChange(
          wrapper,
          '[data-testid="activity-calculation-radio-group"]',
          activityCalculation,
        );

        assert.calledWith(
          fakeUpdateAutoGradingConfig,
          sinon.match({ activity_calculation: activityCalculation }),
        );
      });

      it('renders inputs based on activity calculation value', () => {
        fakeAutoGradingConfig.activity_calculation = activityCalculation;

        const wrapper = createComponent();
        const inputs = wrapper.find('AnnotationsGoalInput');
        const firstInput = inputs.first();

        assert.equal(inputs.length, activityCalculation === 'separate' ? 2 : 1);
        assert.equal(
          firstInput.text(),
          `Annotations${activityCalculation === 'cumulative' ? ' and replies' : ''}Goal`,
        );
      });
    });

    ['all_or_nothing', 'scaled'].forEach(gradingType => {
      it('updates config when changing grading type', () => {
        const wrapper = createComponent();

        dispatchOnChange(
          wrapper,
          '[data-testid="grading-type-radio-group"]',
          gradingType,
        );

        assert.calledWith(
          fakeUpdateAutoGradingConfig,
          sinon.match({ grading_type: gradingType }),
        );
      });

      it('renders different input label depending on grading type value', () => {
        fakeAutoGradingConfig.grading_type = gradingType;

        const wrapper = createComponent();
        const input = wrapper.find('AnnotationsGoalInput').first();

        assert.isTrue(
          input
            .text()
            .endsWith(gradingType === 'all_or_nothing' ? 'Minimum' : 'Goal'),
        );
      });
    });

    [
      {
        inputIndex: 0,
        value: '15',
        expectedConfig: { required_annotations: 15 },
      },
      {
        inputIndex: 1,
        value: '3',
        expectedConfig: { required_replies: 3 },
      },
    ].forEach(({ inputIndex, value, expectedConfig }) => {
      it('updates config when inputs change', () => {
        fakeAutoGradingConfig.activity_calculation = 'separate';

        const wrapper = createComponent();
        const inputs = wrapper.find('AnnotationsGoalInput');

        act(() =>
          inputs.at(inputIndex).find('Input').props().onChange({
            target: { value },
          }),
        );

        assert.calledWith(
          fakeUpdateAutoGradingConfig,
          sinon.match(expectedConfig),
        );
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: 'disabled',
        content: () => createComponent(),
      },
      {
        name: 'enabled',
        content: () => {
          fakeAutoGradingConfig.enabled = true;
          return createComponent();
        },
      },
    ]),
  );
});
