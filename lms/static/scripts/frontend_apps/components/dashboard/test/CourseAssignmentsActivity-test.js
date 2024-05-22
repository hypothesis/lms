import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import CourseAssignmentsActivity, {
  $imports,
} from '../CourseAssignmentsActivity';

describe('CourseAssignmentsActivity', () => {
  const assignments = [
    {
      id: 2,
      title: 'b',
      stats: {
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
    },
    {
      id: 1,
      title: 'a',
      stats: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
    },
    {
      id: 3,
      title: 'c',
      stats: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 5,
        replies: 100,
      },
    },
  ];

  let fakeUseAPIFetch;
  let fakeConfig;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().callsFake(url => ({
      isLoading: false,
      data: url.endsWith('stats') ? assignments : { title: 'The title' },
    }));
    fakeConfig = {
      dashboard: {
        routes: {
          course: '/dashboard/api/course/:course_id',
          course_assignment_stats: '/dashboard/api/course/:course_id/stats',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        useAPIFetch: fakeUseAPIFetch,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <CourseAssignmentsActivity />
      </Config.Provider>,
    );
  }

  it('shows loading indicators while data is loading', () => {
    fakeUseAPIFetch.returns({ isLoading: true });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('DataTable');

    assert.equal(titleElement.text(), 'Loading...');
    assert.isTrue(tableElement.prop('loading'));
  });

  it('shows error if loading data fails', () => {
    fakeUseAPIFetch.returns({ error: new Error('Something failed') });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('DataTable');

    assert.equal(titleElement.text(), 'Could not load course title');
    assert.equal(
      tableElement.prop('emptyMessage'),
      'Could not load assignments',
    );
  });

  it('shows expected title', () => {
    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('DataTable');
    const expectedTitle = 'The title';

    assert.equal(titleElement.text(), expectedTitle);
    assert.equal(tableElement.prop('title'), expectedTitle);
  });

  it('shows empty assignments message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('DataTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No assignments found');
  });

  [
    {
      orderToSet: { field: 'annotations', direction: 'descending' },
      expectedAssignments: [
        {
          id: 2,
          title: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          id: 3,
          title: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          id: 1,
          title: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
      ],
    },
    {
      orderToSet: { field: 'replies', direction: 'ascending' },
      expectedAssignments: [
        {
          id: 2,
          title: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          id: 1,
          title: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          id: 3,
          title: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ],
    },
    {
      orderToSet: { field: 'last_activity', direction: 'descending' },
      expectedAssignments: [
        {
          id: 1,
          title: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          id: 3,
          title: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          id: 2,
          title: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
      ],
    },
  ].forEach(({ orderToSet, expectedAssignments }) => {
    it('orders assignments on order change', () => {
      const wrapper = createComponent();
      const getRows = () => wrapper.find('DataTable').prop('rows');
      const getOrder = () => wrapper.find('DataTable').prop('order');
      const setOrder = order => {
        wrapper.find('DataTable').props().onOrderChange(order);
        wrapper.update();
      };

      // Initially, assignments are ordered by title
      assert.deepEqual(getOrder(), {
        field: 'title',
        direction: 'ascending',
      });
      assert.deepEqual(getRows(), [
        {
          id: 1,
          title: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          id: 2,
          title: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          id: 3,
          title: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ]);

      setOrder(orderToSet);
      assert.deepEqual(getOrder(), orderToSet);
      assert.deepEqual(getRows(), expectedAssignments);
    });
  });

  [
    { fieldName: 'title', expectedValue: 'Frog dissection' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    { fieldName: 'last_activity', expectedValue: '2024-01-01 10:35' },
  ].forEach(({ fieldName, expectedValue }) => {
    it('renders every field as expected', () => {
      const assignmentStats = {
        id: 123,
        title: 'Frog dissection',
        last_activity: '2024-01-01T10:35:18',
        annotations: 37,
        replies: 25,
      };
      const wrapper = createComponent();

      const item = wrapper
        .find('DataTable')
        .props()
        .renderItem(assignmentStats, fieldName);

      if (fieldName === 'last_activity') {
        assert.equal(item, expectedValue);
        return;
      }

      const itemWrapper = mount(item);
      assert.equal(itemWrapper.text(), expectedValue);

      if (fieldName === 'title') {
        assert.equal(itemWrapper.prop('href'), '/assignment/123');
      }
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
