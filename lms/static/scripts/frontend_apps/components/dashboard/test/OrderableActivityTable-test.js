import { mount } from 'enzyme';

import OrderableActivityTable from '../OrderableActivityTable';

describe('OrderableActivityTable', () => {
  const rows = [
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
  ];

  function createComponent(defaultOrderField = 'display_name') {
    return mount(
      <OrderableActivityTable
        rows={rows}
        columnNames={{
          display_name: 'Name',
          last_activity: 'Last activity',
          annotations: 'Annotations',
          replies: 'Replies',
        }}
        defaultOrderField={defaultOrderField}
      />,
    );
  }

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
    it('reorders students on order change', () => {
      const wrapper = createComponent();
      const getRows = () => wrapper.find('DataTable').prop('rows');
      const getOrder = () => wrapper.find('DataTable').prop('order');
      const setOrder = order => {
        wrapper.find('DataTable').props().onOrderChange(order);
        wrapper.update();
      };

      // Initially ordered by name
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
});
