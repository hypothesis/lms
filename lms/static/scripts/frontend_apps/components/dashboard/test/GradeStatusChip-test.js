import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import GradeStatusChip from '../GradeStatusChip';

describe('GradeStatusChip', () => {
  function renderComponent(grade) {
    return mount(<GradeStatusChip grade={grade} />);
  }

  [0, 0.2, 0.48, 0.77, 0.92, 1].forEach(grade => {
    it('renders valid grades as percentage', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${grade * 100}%`);
    });
  });

  [-2, 2].forEach(grade => {
    it('renders invalid grades verbatim', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${grade * 100}`);
    });
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
    ]),
  );
});
