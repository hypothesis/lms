import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import CourseActivity, { $imports } from '../CourseActivity';

describe('CourseActivity', () => {
  const assignments = [
    {
      id: 2,
      title: 'b',
      annotation_metrics: {
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
    },
    {
      id: 1,
      title: 'a',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
    },
    {
      id: 3,
      title: 'c',
      annotation_metrics: {
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
      data: url.endsWith('stats') ? { assignments } : { title: 'The title' },
    }));
    fakeConfig = {
      dashboard: {
        routes: {
          course: '/api/dashboard/course/:course_id',
          course_assignments_metrics: '/api/dashboard/course/:course_id/stats',
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
        <CourseActivity />
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

    assert.equal(titleElement.text(), 'Could not load course title');
    assert.equal(
      tableElement.prop('emptyMessage'),
      'Could not load assignments',
    );
  });

  it('shows expected title', () => {
    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');
    const expectedTitle = 'Course: The title';

    assert.equal(titleElement.text(), expectedTitle);
    assert.equal(tableElement.prop('title'), expectedTitle);
  });

  it('shows empty assignments message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No assignments found');
  });

  it('flattens assignments to table rows', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.deepEqual(tableElement.prop('rows'), [
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
    ]);
  });

  [
    { fieldName: 'title', expectedValue: 'Frog dissection' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    {
      fieldName: 'last_activity',
      expectedValue: '2024-01-01T10:35:18',
    },
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
        .find('OrderableActivityTable')
        .props()
        .renderItem(assignmentStats, fieldName);

      const itemWrapper = mount(item);

      if (fieldName === 'last_activity') {
        assert.equal(itemWrapper.prop('date'), expectedValue);
        return;
      }

      assert.equal(itemWrapper.text(), expectedValue);

      if (fieldName === 'title') {
        assert.equal(itemWrapper.prop('href'), '/assignments/123');
      }
    });
  });

  [12, 35, 1, 500].forEach(id => {
    it('builds expected href for row confirmation', () => {
      const wrapper = createComponent();
      const href = wrapper
        .find('OrderableActivityTable')
        .props()
        .navigateOnConfirmRow({ id });

      assert.equal(href, `/assignments/${id}`);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
