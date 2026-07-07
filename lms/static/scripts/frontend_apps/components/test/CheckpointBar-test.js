import {
  checkAccessibility,
  mockImportedComponents,
  mount,
} from '@hypothesis/frontend-testing';

import CheckpointBar, { $imports } from '../CheckpointBar';

describe('CheckpointBar', () => {
  const checkpoint = {
    revealed: false,
    revealDate: null,
    revealUrl: '/api/assignments/1/checkpoint/reveal',
  };

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  const render = (props = {}) =>
    mount(<CheckpointBar checkpoint={checkpoint} {...props} />);

  it('renders the checkpoint type', () => {
    const wrapper = render();
    assert.include(
      wrapper.find('[data-testid="checkpoint-type"]').text(),
      'Manual',
    );
  });

  it('passes the checkpoint config to the reveal button', () => {
    const wrapper = render();
    const button = wrapper.find('RevealAnnotationsButton');
    assert.isTrue(button.exists());
    assert.deepEqual(button.prop('checkpoint'), checkpoint);
  });

  it('does not render a due date when none is provided', () => {
    const wrapper = render();
    assert.isFalse(wrapper.exists('[data-testid="checkpoint-due-date"]'));
  });

  it('renders the due date when provided', () => {
    const wrapper = render({ dueDate: '2026-07-01T10:00:00' });
    assert.isTrue(wrapper.exists('[data-testid="checkpoint-due-date"]'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => render(),
    }),
  );
});
