import { mount } from 'enzyme';

import StudentsActivityTable from '../StudentsActivityTable';

describe('StudentsActivityTable', () => {
  function createComponent({
    students = [],
    title = 'The assignment',
    loading,
  } = {}) {
    return mount(
      <StudentsActivityTable
        students={students}
        assignment={{ title }}
        loading={loading}
      />,
    );
  }

  ['foo', 'Assignment', 'Hello World'].forEach(title => {
    it('shows expected title', () => {
      const wrapper = createComponent({ title });
      const titleElement = wrapper.find('[data-testid="title"]');
      const tableElement = wrapper.find('DataTable');
      const expectedTitle = `Student activity for assignment "${title}"`;

      assert.equal(titleElement.text(), expectedTitle);
      assert.equal(tableElement.prop('title'), expectedTitle);
    });
  });

  [true, false].forEach(loading => {
    it('sets loading state in table', () => {
      const wrapper = createComponent({ loading });
      assert.equal(wrapper.find('DataTable').prop('loading'), loading);
    });
  });

  [
    {
      orderToSet: { field: 'annotations', direction: 'descending' },
      expectedStudents: [
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
      ],
    },
    {
      orderToSet: { field: 'replies', direction: 'ascending' },
      expectedStudents: [
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ],
    },
    {
      orderToSet: { field: 'last_activity', direction: 'descending' },
      expectedStudents: [
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
      ],
    },
  ].forEach(({ orderToSet, expectedStudents }) => {
    it('orders students on order change', () => {
      const wrapper = createComponent({
        students: [
          {
            display_name: 'b',
            last_activity: '2020-01-01T00:00:00',
            annotations: 8,
            replies: 0,
          },
          {
            display_name: 'a',
            last_activity: '2020-01-02T00:00:00',
            annotations: 3,
            replies: 20,
          },
          {
            display_name: 'c',
            last_activity: '2020-01-02T00:00:00',
            annotations: 5,
            replies: 100,
          },
        ],
      });
      const getRows = () => wrapper.find('DataTable').prop('rows');
      const getOrder = () => wrapper.find('DataTable').prop('order');
      const setOrder = order => {
        wrapper.find('DataTable').props().onOrderChange(order);
        wrapper.update();
      };

      // Initially, students are ordered by name
      assert.deepEqual(getOrder(), {
        field: 'display_name',
        direction: 'ascending',
      });
      assert.deepEqual(getRows(), [
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ]);

      setOrder(orderToSet);
      assert.deepEqual(getOrder(), orderToSet);
      assert.deepEqual(getRows(), expectedStudents);
    });
  });

  [
    { fieldName: 'display_name', expectedValue: 'Jane Doe' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    { fieldName: 'last_activity', expectedValue: '2024-01-01 10:35' },
  ].forEach(({ fieldName, expectedValue }) => {
    it('renders every field as expected', () => {
      const studentStats = {
        display_name: 'Jane Doe',
        last_activity: '2024-01-01T10:35:18',
        annotations: 37,
        replies: 25,
      };
      const wrapper = createComponent();

      const item = wrapper
        .find('DataTable')
        .props()
        .renderItem(studentStats, fieldName);
      const value = typeof item === 'string' ? item : mount(item).text();

      assert.equal(value, expectedValue);
    });
  });
});
