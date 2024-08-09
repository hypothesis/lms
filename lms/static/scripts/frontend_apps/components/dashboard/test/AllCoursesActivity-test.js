import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';
import sinon from 'sinon';

import { Config } from '../../../config';
import { formatDateTime } from '../../../utils/date';
import AllCoursesActivity, { $imports } from '../AllCoursesActivity';

describe('AllCoursesActivity', () => {
  const courses = [
    {
      id: 1,
      title: 'Course A',
      course_metrics: {
        assignments: 10,
        last_launched: '2020-01-02T00:00:00',
      },
    },
    {
      id: 2,
      title: 'Course B',
      course_metrics: {
        assignments: 0,
        last_launched: null,
      },
    },
  ];
  let wrappers;

  let fakeUseAPIFetch;
  let fakeUseParams;
  let fakeConfig;

  beforeEach(() => {
    // Reset query string before every test
    history.replaceState(null, '', '?');

    wrappers = [];

    fakeUseAPIFetch = sinon.stub().returns({
      isLoading: false,
      data: { courses },
    });
    fakeUseParams = sinon.stub().returns({});
    fakeConfig = {
      dashboard: {
        routes: {
          courses_metrics: '/api/courses/metrics',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      // Do not mock FormattedDate, for consistency when checking
      // rendered values in different columns
      './FormattedDate': true,
    });
    $imports.$mock({
      '../../utils/api': {
        useAPIFetch: fakeUseAPIFetch,
      },
      'wouter-preact': {
        useParams: fakeUseParams,
      },
    });
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    $imports.$restore();
  });

  function createComponent() {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <AllCoursesActivity />
      </Config.Provider>,
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  it('sets loading state in table while data is loading', () => {
    fakeUseAPIFetch.returns({ isLoading: true });

    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.isTrue(tableElement.prop('loading'));
  });

  it('shows error if loading data fails', () => {
    fakeUseAPIFetch.returns({ error: new Error('Something failed') });

    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'Could not load courses');
  });

  it('shows empty courses message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No courses found');
  });

  courses.forEach(({ id, title, course_metrics }) => {
    const courseRow = {
      id,
      title,
      ...course_metrics,
    };
    const renderItem = (wrapper, field) =>
      wrapper
        .find('OrderableActivityTable')
        .props()
        .renderItem(courseRow, field);

    it('renders course links', () => {
      const wrapper = createComponent();
      const item = renderItem(wrapper, 'title');
      const itemWrapper = mount(item);

      assert.equal(itemWrapper.text(), title);
      assert.equal(itemWrapper.prop('href'), `/courses/${id}`);
    });

    it('renders last launched date', () => {
      const wrapper = createComponent();
      const { last_launched } = courseRow;
      const item = renderItem(wrapper, 'last_launched');
      const itemText = last_launched ? mount(item).text() : '';

      assert.equal(
        itemText,
        last_launched ? formatDateTime(new Date(last_launched)) : '',
      );
    });

    it('renders assignments', () => {
      const wrapper = createComponent();
      const item = renderItem(wrapper, 'assignments');
      const itemWrapper = mount(item);
      const { assignments } = courseRow;

      assert.equal(itemWrapper.text(), `${assignments}`);
    });
  });

  [12, 35, 1, 500].forEach(id => {
    it('builds expected href for row confirmation', () => {
      const wrapper = createComponent();
      const href = wrapper
        .find('OrderableActivityTable')
        .props()
        .navigateOnConfirmRow({ id });

      assert.equal(href, `/courses/${id}`);
    });
  });

  it('allows metrics to be filtered', () => {
    const wrapper = createComponent();
    const filters = wrapper.find('DashboardActivityFilters');
    const updateFilter = (prop, arg) => {
      act(() => filters.prop(prop).onChange(arg));
      wrapper.update();
    };
    const assertCoursesFetched = query =>
      assert.calledWith(fakeUseAPIFetch.lastCall, sinon.match.string, query);

    // Every time the filters callbacks are invoked, the component will
    // re-render and re-fetch metrics with updated query.
    updateFilter('students', ['123', '456']);
    assertCoursesFetched({
      h_userid: ['123', '456'],
      assignment_id: [],
      course_id: [],
      org_public_id: undefined,
    });

    updateFilter('assignments', ['1', '2']);
    assertCoursesFetched({
      h_userid: [],
      assignment_id: ['1', '2'],
      course_id: [],
      org_public_id: undefined,
    });

    updateFilter('courses', ['3', '8', '9']);
    assertCoursesFetched({
      h_userid: [],
      assignment_id: [],
      course_id: ['3', '8', '9'],
      org_public_id: undefined,
    });
  });

  context('when `organizationPublicId` is present in URL params', () => {
    beforeEach(() => {
      fakeUseParams.returns({ organizationPublicId: 'the-org-public-id' });
    });

    it('propagates org_public_id to API calls', () => {
      createComponent();

      assert.calledWith(
        fakeUseAPIFetch.lastCall,
        sinon.match.string,
        sinon.match({ org_public_id: 'the-org-public-id' }),
      );
    });
  });

  it('allows filters to be cleared', () => {
    const wrapper = createComponent();
    const filters = wrapper.find('DashboardActivityFilters');

    act(() => filters.props().onClearSelection());
    wrapper.update();

    assert.calledWith(fakeUseAPIFetch.lastCall, sinon.match.string, {
      h_userid: [],
      assignment_id: [],
      course_id: [],
      org_public_id: undefined,
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
