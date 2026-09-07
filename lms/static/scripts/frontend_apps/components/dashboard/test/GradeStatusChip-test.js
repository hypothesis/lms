import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import GradeStatusChip from '../GradeStatusChip';

describe('GradeStatusChip', () => {
  function renderComponent(grade, muted) {
    return mount(<GradeStatusChip grade={grade} muted={muted} />);
  }

  [
    [0, '0'],
    [0.2, '20'],
    [0.33330004, '33.33'],
    [0.48, '48'],
    [0.77, '77'],
    [0.92, '92'],
    [1, '100'],
  ].forEach(([grade, expected]) => {
    it('renders valid grades as percentage', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${expected}%`);
    });
  });

  [-2, 2].forEach(grade => {
    it('renders invalid grades verbatim', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${grade * 100}`);
    });
  });

  it('renders a muted grade in grey, keeping the percentage', () => {
    const wrapper = renderComponent(1, true);

    assert.equal(wrapper.text(), '100%');
    assert.isTrue(wrapper.find('div').hasClass('bg-grey-3'));
    assert.isFalse(wrapper.find('div').hasClass('bg-green-dark'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: '100',
        content: () => renderComponent(1),
      },
      {
        name: '80',
        content: () => renderComponent(0.8),
      },
      {
        name: '68',
        content: () => renderComponent(0.68),
      },
      {
        name: '38',
        content: () => renderComponent(0.38),
      },
      {
        name: '0',
        content: () => renderComponent(0),
      },
      {
        name: '-20',
        content: () => renderComponent(-0.2),
      },
      {
        name: '150',
        content: () => renderComponent(1.5),
      },
      {
        name: 'muted',
        content: () => renderComponent(0.8, true),
      },
    ]),
  );
});
