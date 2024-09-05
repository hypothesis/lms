import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import GradeStatusChip from '../GradeStatusChip';

describe('GradeStatusChip', () => {
  function renderComponent(grade) {
    return mount(<GradeStatusChip grade={grade} />);
  }

  [0, 20, 48, 77, 92, 100].forEach(grade => {
    it('renders valid grades as percentage', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${grade}%`);
    });
  });

  [-20, 150].forEach(grade => {
    it('renders invalid grades verbatim', () => {
      const wrapper = renderComponent(grade);
      assert.equal(wrapper.text(), `${grade}`);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility([
      {
        name: '100',
        content: () => renderComponent(100),
      },
      {
        name: '80',
        content: () => renderComponent(80),
      },
      {
        name: '68',
        content: () => renderComponent(68),
      },
      {
        name: '38',
        content: () => renderComponent(38),
      },
      {
        name: '0',
        content: () => renderComponent(0),
      },
      {
        name: '-20',
        content: () => renderComponent(-20),
      },
      {
        name: '150',
        content: () => renderComponent(150),
      },
    ]),
  );
});
