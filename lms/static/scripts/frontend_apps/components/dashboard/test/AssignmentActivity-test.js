import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import { formatDateTime } from '../../../utils/date';
import AssignmentActivity, { $imports } from '../AssignmentActivity';

describe('AssignmentActivity', () => {
  const students = [
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

  let fakeUseAPIFetch;
  let fakeConfig;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().callsFake(url => ({
      isLoading: false,
      data: url.endsWith('stats')
        ? students
        : {
            title: 'The title',
            course: {
              title: 'The course',
            },
          },
    }));
    fakeConfig = {
      dashboard: {
        routes: {
          assignment: '/api/assignments/:assignment_id',
          assignment_stats: '/api/assignments/:assignment_id/stats',
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
        <AssignmentActivity />
      </Config.Provider>,
    );
  }

  it('shows loading indicators while data is loading', () => {
    fakeUseAPIFetch.returns({ isLoading: true });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(titleElement.text(), 'Loading...');
    assert.isTrue(tableElement.prop('loading'));
  });

  it('shows error if loading data fails', () => {
    fakeUseAPIFetch.returns({ error: new Error('Something failed') });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(titleElement.text(), 'Could not load assignment title');
    assert.equal(tableElement.prop('emptyMessage'), 'Could not load students');
  });

  it('shows expected title', () => {
    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');
    const expectedTitle = 'Assignment: The title';

    assert.equal(titleElement.text(), expectedTitle);
    assert.equal(tableElement.prop('title'), expectedTitle);
  });

  it('shows empty students message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No students found');
  });

  [
    { fieldName: 'display_name', expectedValue: 'Jane Doe' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    {
      fieldName: 'last_activity',
      expectedValue: formatDateTime(new Date('2024-01-01T10:35:18')),
    },
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
        .find('OrderableActivityTable')
        .props()
        .renderItem(studentStats, fieldName);
      const value = typeof item === 'string' ? item : mount(item).text();

      assert.equal(value, expectedValue);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
