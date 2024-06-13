import { mount } from 'enzyme';

import OrderableActivityTable, { $imports } from '../OrderableActivityTable';

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
  let fakeNavigate;

  beforeEach(() => {
    fakeNavigate = sinon.stub();

    $imports.$mock({
      'wouter-preact': {
        useLocation: sinon.stub().returns(['', fakeNavigate]),
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent({ navigateOnConfirmRow } = {}) {
    return mount(
      <OrderableActivityTable
        rows={rows}
        columnNames={{
          display_name: 'Name',
          last_activity: 'Last activity',
          annotations: 'Annotations',
          replies: 'Replies',
        }}
        defaultOrderField="display_name"
        navigateOnConfirmRow={navigateOnConfirmRow}
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

  it('navigates when a row is confirmed', () => {
    const navigateOnConfirmRow = sinon.stub().returns('/foo/bar');
    const wrapper = createComponent({ navigateOnConfirmRow });

    wrapper.find('DataTable').props().onConfirmRow();

    assert.called(navigateOnConfirmRow);
    assert.calledWith(fakeNavigate, '/foo/bar');
  });
});
