import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import AutoGradingConfigurator, {
  defaultAutoGradingConfig,
  fromAPIConfig,
  toAPIConfig,
} from '../AutoGradingConfigurator';

/** The two phases a "Paced Social Annotation" assignment is graded in. */
const gradingPhases = [
  {
    label: 'Checkpoint',
    description: 'Applies to activity before the Checkpoint',
  },
  {
    label: 'Due Date',
    description: 'Applies to activity after the Checkpoint',
  },
];

describe('AutoGradingConfigurator', () => {
  let fakeAutoGradingConfig;
  let fakeUpdateAutoGradingConfig;

  beforeEach(() => {
    fakeAutoGradingConfig = {
      mode: 'single',
      grading_type: 'scaled',
      activity_calculation: 'cumulative',
      single: { required_annotations: 1 },
      phases: [],
    };
    fakeUpdateAutoGradingConfig = sinon.stub();
  });

  function createComponent(props = {}) {
    return mount(
      <AutoGradingConfigurator
        config={fakeAutoGradingConfig}
        onChange={fakeUpdateAutoGradingConfig}
        {...props}
      />,
    );
  }

  /** Mount an assignment which can be graded phase by phase. */
  function createPacedComponent(props = {}) {
    return createComponent({ gradingPhases, ...props });
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
        expectedGoals: { required_annotations: 15 },
      },
      {
        inputIndex: 1,
        value: '3',
        expectedGoals: { required_replies: 3 },
      },
    ].forEach(({ inputIndex, value, expectedGoals }) => {
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
          sinon.match({ single: sinon.match(expectedGoals) }),
        );
      });
    });

    context('when the assignment cannot be paced', () => {
      it('offers no grading mode and no phases', () => {
        const wrapper = createComponent();

        assert.isFalse(
          wrapper.exists('[data-testid="grading-mode-radio-group"]'),
        );
        assert.isFalse(wrapper.exists('TabList'));
      });

      it('ignores a single grading phase, which has nothing to split', () => {
        const wrapper = createComponent({
          gradingPhases: gradingPhases.slice(0, 1),
        });

        assert.isFalse(
          wrapper.exists('[data-testid="grading-mode-radio-group"]'),
        );
        assert.isFalse(wrapper.exists('TabList'));
      });
    });

    context('when the assignment can be paced', () => {
      it('offers the grading mode', () => {
        const wrapper = createPacedComponent();

        assert.isTrue(
          wrapper.exists('[data-testid="grading-mode-radio-group"]'),
        );
      });

      ['single', 'paced'].forEach(mode => {
        it('updates config when changing grading mode', () => {
          const wrapper = createPacedComponent();

          dispatchOnChange(
            wrapper,
            '[data-testid="grading-mode-radio-group"]',
            mode,
          );

          assert.calledWith(fakeUpdateAutoGradingConfig, sinon.match({ mode }));
        });
      });

      it('shows no phases while the assignment gets a single grade', () => {
        const wrapper = createPacedComponent();

        assert.isFalse(wrapper.exists('TabList'));
        assert.isFalse(wrapper.exists('[data-testid="phase-description"]'));
      });

      context('with paced grades', () => {
        beforeEach(() => {
          fakeAutoGradingConfig.mode = 'paced';
          fakeAutoGradingConfig.phases = [
            { required_annotations: 2 },
            { required_annotations: 5 },
          ];
        });

        it('renders one tab per grading phase', () => {
          const wrapper = createPacedComponent();
          const tabs = wrapper.find('Tab');

          assert.equal(tabs.length, 2);
          assert.equal(tabs.at(0).text(), 'Checkpoint');
          assert.equal(tabs.at(1).text(), 'Due Date');
        });

        it('shows the goals of the selected phase', () => {
          const wrapper = createPacedComponent();

          assert.equal(
            wrapper.find('AnnotationsGoalInput Input').prop('value'),
            2,
          );
          assert.equal(
            wrapper.find('[data-testid="phase-description"]').text(),
            gradingPhases[0].description,
          );

          wrapper.find('button[data-testid="phase-tab-1"]').simulate('click');

          assert.equal(
            wrapper.find('AnnotationsGoalInput Input').prop('value'),
            5,
          );
          assert.equal(
            wrapper.find('[data-testid="phase-description"]').text(),
            gradingPhases[1].description,
          );
        });

        it('updates the goals of the selected phase only', () => {
          const wrapper = createPacedComponent();

          wrapper.find('button[data-testid="phase-tab-1"]').simulate('click');
          act(() =>
            wrapper
              .find('AnnotationsGoalInput Input')
              .props()
              .onChange({
                target: { value: '7' },
              }),
          );

          assert.calledWith(
            fakeUpdateAutoGradingConfig,
            sinon.match({
              phases: [
                sinon.match({ required_annotations: 2 }),
                sinon.match({ required_annotations: 7 }),
              ],
            }),
          );
        });

        it('leaves a phase the config lacks unset', () => {
          // An assignment saved as a single grade only carries one phase.
          fakeAutoGradingConfig.phases = [{ required_annotations: 2 }];

          const wrapper = createPacedComponent();

          // Flagged as unset before it is ever opened, rather than carrying a
          // goal the instructor never chose.
          assert.isTrue(wrapper.exists('[data-testid="phase-unset-1"]'));

          wrapper.find('button[data-testid="phase-tab-1"]').simulate('click');

          assert.equal(
            wrapper.find('AnnotationsGoalInput Input').prop('value'),
            0,
          );
        });

        [
          {
            when: 'a cumulative goal is missing',
            activityCalculation: 'cumulative',
            phases: [{ required_annotations: 2 }, { required_annotations: 0 }],
            unset: true,
          },
          {
            when: 'both separate goals are missing',
            activityCalculation: 'separate',
            phases: [
              { required_annotations: 2 },
              { required_annotations: 0, required_replies: 0 },
            ],
            unset: true,
          },
          {
            // The replies input allows zero, so the annotations goal is the
            // one that has to be filled in either way.
            when: 'only the separate replies goal is set',
            activityCalculation: 'separate',
            phases: [
              { required_annotations: 2 },
              { required_annotations: 0, required_replies: 3 },
            ],
            unset: true,
          },
          {
            when: 'the goals are set',
            activityCalculation: 'cumulative',
            phases: [{ required_annotations: 2 }, { required_annotations: 5 }],
            unset: false,
          },
        ].forEach(({ when, activityCalculation, phases, unset }) => {
          it(`marks an unselected phase as not set when ${when}`, () => {
            fakeAutoGradingConfig.activity_calculation = activityCalculation;
            fakeAutoGradingConfig.phases = phases;

            const wrapper = createPacedComponent();

            assert.equal(
              wrapper.exists('[data-testid="phase-unset-1"]'),
              unset,
            );
          });
        });

        it('never marks the selected phase as not set', () => {
          fakeAutoGradingConfig.phases = [
            { required_annotations: 0 },
            { required_annotations: 0 },
          ];

          const wrapper = createPacedComponent();

          assert.isFalse(wrapper.exists('[data-testid="phase-unset-0"]'));
          assert.isTrue(wrapper.exists('[data-testid="phase-unset-1"]'));
        });

        context('validating the goals', () => {
          /**
           * Mount a paced assignment and return the handle its parent
           * validates through.
           */
          function createComponentWithHandle(props = {}) {
            const configuratorRef = { current: null };
            const wrapper = createPacedComponent({ configuratorRef, ...props });
            const validate = () => {
              let valid;
              act(() => {
                valid = configuratorRef.current.validate();
              });
              wrapper.update();
              return valid;
            };
            return { wrapper, validate };
          }

          it('accepts phases which all have a goal', () => {
            fakeAutoGradingConfig.phases = [
              { required_annotations: 2 },
              { required_annotations: 5 },
            ];
            const { wrapper, validate } = createComponentWithHandle();

            assert.isTrue(validate());
            assert.isFalse(wrapper.exists('[data-testid="phase-goal-error"]'));
          });

          it('refuses a phase left without a goal and switches to it', () => {
            fakeAutoGradingConfig.phases = [
              { required_annotations: 2 },
              { required_annotations: 0 },
            ];
            const { wrapper, validate } = createComponentWithHandle();

            assert.isFalse(validate());
            // The offending phase is now the one on screen, so the message
            // lands next to the field it is about.
            assert.equal(
              wrapper.find('[data-testid="phase-description"]').text(),
              gradingPhases[1].description,
            );
            assert.isTrue(wrapper.exists('[data-testid="phase-goal-error"]'));
          });

          it('refuses a phase the instructor never opened', () => {
            // Nothing edited at all: every phase is still unset.
            fakeAutoGradingConfig.phases = [];
            const { wrapper, validate } = createComponentWithHandle();

            assert.isFalse(validate());
            assert.equal(
              wrapper.find('[data-testid="phase-description"]').text(),
              gradingPhases[0].description,
            );
          });

          it('says nothing until a submit is actually refused', () => {
            fakeAutoGradingConfig.phases = [];
            const { wrapper } = createComponentWithHandle();

            // An empty phase the instructor simply hasn't reached yet is not
            // an error.
            assert.isFalse(wrapper.exists('[data-testid="phase-goal-error"]'));
          });

          it('stops complaining once the goal is entered', () => {
            fakeAutoGradingConfig.phases = [
              { required_annotations: 0 },
              { required_annotations: 5 },
            ];
            const { wrapper, validate } = createComponentWithHandle();

            assert.isFalse(validate());
            assert.isTrue(wrapper.exists('[data-testid="phase-goal-error"]'));

            fakeAutoGradingConfig.phases[0] = { required_annotations: 3 };
            wrapper.setProps({ config: fakeAutoGradingConfig });

            assert.isFalse(wrapper.exists('[data-testid="phase-goal-error"]'));
          });

          it('leaves a single grade to the browser, which sees its one input', () => {
            fakeAutoGradingConfig.mode = 'single';
            fakeAutoGradingConfig.phases = [];
            const { validate } = createComponentWithHandle();

            assert.isTrue(validate());
          });

          it('has nothing to check while auto grading is off', () => {
            fakeAutoGradingConfig.enabled = false;
            fakeAutoGradingConfig.phases = [];
            const { validate } = createComponentWithHandle();

            assert.isTrue(validate());
          });
        });
      });
    });
  });

  describe('toAPIConfig', () => {
    it('sends one config for a single grade', () => {
      assert.deepEqual(
        toAPIConfig(
          {
            enabled: true,
            mode: 'single',
            grading_type: 'scaled',
            activity_calculation: 'cumulative',
            single: { required_annotations: 4 },
            phases: [{ required_annotations: 2 }],
          },
          2,
        ),
        {
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          required_annotations: 4,
        },
      );
    });

    it('sends one config per phase for paced grades, sharing the grading options', () => {
      assert.deepEqual(
        toAPIConfig(
          {
            enabled: true,
            mode: 'paced',
            grading_type: 'all_or_nothing',
            activity_calculation: 'separate',
            single: { required_annotations: 4 },
            phases: [
              { required_annotations: 2, required_replies: 1 },
              { required_annotations: 5 },
            ],
          },
          2,
        ),
        [
          {
            grading_type: 'all_or_nothing',
            activity_calculation: 'separate',
            required_annotations: 2,
            required_replies: 1,
          },
          {
            grading_type: 'all_or_nothing',
            activity_calculation: 'separate',
            required_annotations: 5,
          },
        ],
      );
    });

    it('still sends one config per phase when no goal was touched', () => {
      // `validate` refuses this before a submit can reach here, but the shape
      // has to stay one config per phase regardless: an empty list would read
      // as "no auto grading" and delete the config.
      assert.deepEqual(
        toAPIConfig(
          {
            enabled: true,
            mode: 'paced',
            grading_type: 'scaled',
            activity_calculation: 'cumulative',
            single: { required_annotations: 4 },
            phases: [],
          },
          2,
        ),
        [
          {
            grading_type: 'scaled',
            activity_calculation: 'cumulative',
            required_annotations: 0,
          },
          {
            grading_type: 'scaled',
            activity_calculation: 'cumulative',
            required_annotations: 0,
          },
        ],
      );
    });

    it('sends a single config when there are no phases to pace', () => {
      assert.deepEqual(
        toAPIConfig(
          {
            enabled: true,
            mode: 'paced',
            grading_type: 'scaled',
            activity_calculation: 'cumulative',
            single: { required_annotations: 4 },
            phases: [],
          },
          0,
        ),
        {
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          required_annotations: 4,
        },
      );
    });
  });

  describe('fromAPIConfig', () => {
    it('reads a single config back as a single grade', () => {
      assert.deepEqual(
        fromAPIConfig({
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          required_annotations: 4,
        }),
        {
          enabled: true,
          mode: 'single',
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          single: { required_annotations: 4 },
          phases: [{ required_annotations: 4 }],
        },
      );
    });

    it('reads no configs back as the defaults', () => {
      assert.deepEqual(fromAPIConfig([]), defaultAutoGradingConfig());
    });

    it('reads several configs back as paced grades', () => {
      const config = fromAPIConfig([
        {
          grading_type: 'all_or_nothing',
          activity_calculation: 'separate',
          required_annotations: 2,
          required_replies: 1,
        },
        {
          grading_type: 'all_or_nothing',
          activity_calculation: 'separate',
          required_annotations: 5,
          required_replies: 3,
        },
      ]);

      assert.equal(config.mode, 'paced');
      assert.equal(config.grading_type, 'all_or_nothing');
      assert.equal(config.activity_calculation, 'separate');
      assert.deepEqual(config.phases, [
        { required_annotations: 2, required_replies: 1 },
        { required_annotations: 5, required_replies: 3 },
      ]);
      // The first phase seeds the single grade, so switching modes starts from
      // something rather than from the default.
      assert.deepEqual(config.single, {
        required_annotations: 2,
        required_replies: 1,
      });
    });

    it('drops a reply goal the backend sends as nothing', () => {
      // `asdict()` sends the key either way, as `null` for a cumulative
      // config. Kept, it reaches a number input as its value and the field
      // renders empty, because a destructuring default only answers to
      // `undefined`.
      const config = fromAPIConfig([
        {
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          required_annotations: 2,
          required_replies: null,
        },
        {
          grading_type: 'scaled',
          activity_calculation: 'cumulative',
          required_annotations: 5,
          required_replies: null,
        },
      ]);

      assert.deepEqual(config.phases, [
        { required_annotations: 2 },
        { required_annotations: 5 },
      ]);
      assert.deepEqual(config.single, { required_annotations: 2 });
    });

    it('keeps a reply goal of zero', () => {
      // Zero is a goal a phase can have: the replies input takes `min={0}`.
      const config = fromAPIConfig({
        grading_type: 'scaled',
        activity_calculation: 'separate',
        required_annotations: 2,
        required_replies: 0,
      });

      assert.deepEqual(config.single, {
        required_annotations: 2,
        required_replies: 0,
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
      {
        name: 'paced grades',
        content: () => {
          fakeAutoGradingConfig.enabled = true;
          fakeAutoGradingConfig.mode = 'paced';
          fakeAutoGradingConfig.phases = [
            { required_annotations: 2 },
            { required_annotations: 5 },
          ];
          return createPacedComponent();
        },
      },
    ]),
  );
});
