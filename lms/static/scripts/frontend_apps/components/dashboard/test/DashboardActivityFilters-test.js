import { MultiSelect } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import { formatDateTime } from '../../../utils/date';
import DashboardActivityFilters, {
  $imports,
} from '../DashboardActivityFilters';

describe('DashboardActivityFilters', () => {
  const courses = [
    {
      id: 1,
      title: 'Course A',
    },
    {
      id: 2,
      title: 'Course B',
    },
  ];
  const assignments = [
    {
      id: 1,
      title: 'Assignment 1',
      created: '2024-08-05T09:55:46.523343',
    },
    {
      id: 2,
      title: 'Assignment 2',
      created: '2024-06-10T09:55:44.701550',
    },
  ];
  const studentsWithName = [
    {
      lms_id: '1',
      h_userid: 'acct:1@lms.hypothes.is',
      display_name: 'First student',
    },
    {
      lms_id: '2',
      h_userid: 'acct:2@lms.hypothes.is',
      display_name: 'Second student',
    },
  ];
  const students = [
    ...studentsWithName,
    {
      lms_id: '123456789',
      h_userid: 'acct:3@lms.hypothes.is',
      display_name: null, // Student with an empty name won't be displayed
    },
  ];

  let fakeUsePaginatedAPIFetch;
  let fakeConfig;
  let onCoursesChange;
  let onAssignmentsChange;
  let onStudentsChange;
  let fakeLoadNextCoursesPage;
  let fakeLoadNextAssignmentsPage;
  let fakeLoadNextStudentsPage;
  let wrappers = [];

  /**
   * @param {object} options
   * @param {boolean} options.isLoading
   * @param {boolean} [options.isLoadingFirstPage] - Defaults to isLoading
   */
  function configureFakeAPIFetch(options) {
    const { isLoading, isLoadingFirstPage = isLoading } = options;

    fakeUsePaginatedAPIFetch.onCall(0).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading ? null : courses,
      loadNextPage: fakeLoadNextCoursesPage,
    });
    fakeUsePaginatedAPIFetch.onCall(1).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading ? null : assignments,
      loadNextPage: fakeLoadNextAssignmentsPage,
    });
    fakeUsePaginatedAPIFetch.onCall(2).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading ? null : students,
      loadNextPage: fakeLoadNextStudentsPage,
    });
  }

  beforeEach(() => {
    fakeLoadNextCoursesPage = sinon.stub();
    fakeLoadNextAssignmentsPage = sinon.stub();
    fakeLoadNextStudentsPage = sinon.stub();
    fakeUsePaginatedAPIFetch = sinon.stub();
    configureFakeAPIFetch({ isLoading: false });

    onCoursesChange = sinon.stub();
    onAssignmentsChange = sinon.stub();
    onStudentsChange = sinon.stub();
    wrappers = [];

    fakeConfig = {
      dashboard: {
        routes: {
          courses: '/api/dashboard/courses',
          assignments: '/api/dashboard/assignments',
          students: '/api/dashboard/students',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        usePaginatedAPIFetch: fakeUsePaginatedAPIFetch,
      },
    });
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    $imports.$restore();
  });

  function createComponent(options = {}) {
    return createComponentWithProps({
      courses: {
        selectedIds: options.selectedCourseIds ?? [],
        onChange: onCoursesChange,
      },
      assignments: {
        selectedIds: options.selectedAssignmentIds ?? [],
        onChange: onAssignmentsChange,
      },
      students: {
        selectedIds: options.selectedStudentIds ?? [],
        onChange: onStudentsChange,
      },
      onClearSelection: options.onClearSelection,
    });
  }

  function createComponentWithProps(props) {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <DashboardActivityFilters {...props} />
      </Config.Provider>,
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  function getSelect(wrapper, id) {
    return wrapper.find(`MultiSelect[data-testid="${id}"]`);
  }

  function getSelectContent(wrapper, id) {
    const content = getSelect(wrapper, id).prop('buttonContent');
    // Wrap content in div, as it could be a fragment with multiple children
    // or a scalar value, which would make the call to `mount` fail
    return mount(<div>{content}</div>).text();
  }

  it('shows loading indicators while loading', () => {
    configureFakeAPIFetch({ isLoading: true });

    const wrapper = createComponent();

    assert.equal(getSelectContent(wrapper, 'courses-select'), '...');
    assert.equal(getSelectContent(wrapper, 'assignments-select'), '...');
    assert.equal(getSelectContent(wrapper, 'students-select'), '...');
  });

  it('shows placeholders when selection is empty', () => {
    const wrapper = createComponent();

    assert.equal(getSelectContent(wrapper, 'courses-select'), 'All courses');
    assert.equal(
      getSelectContent(wrapper, 'assignments-select'),
      'All assignments',
    );
    assert.equal(getSelectContent(wrapper, 'students-select'), 'All students');
  });

  [
    {
      id: 'courses-select',
      expectedOptions: ['All courses', ...courses.map(c => c.title)],
    },
    {
      id: 'assignments-select',
      expectedOptions: [
        'All assignments',
        ...assignments.map(a => `${a.title}${formatDateTime(a.created)}`),
      ],
    },
    {
      id: 'students-select',
      expectedOptions: [
        'All students',
        ...studentsWithName.map(s => s.display_name),
        'Student name unavailable (ID: 12345)',
      ],
      expectedTitles: [undefined, undefined, undefined, 'User ID: 123456789'],
    },
  ].forEach(({ id, expectedOptions, expectedTitles = [] }) => {
    it('renders corresponding options', () => {
      const wrapper = createComponent();
      const select = getSelect(wrapper, id);
      const options = select.find(MultiSelect.Option);

      assert.equal(options.length, expectedOptions.length);
      options.forEach((option, index) => {
        assert.equal(option.text(), expectedOptions[index]);

        if (expectedTitles[index]) {
          assert.equal(
            option.find('[data-testid="option-content-wrapper"]').prop('title'),
            expectedTitles[index],
          );
        }
      });
    });
  });

  [
    {
      id: 'courses-select',
      selection: courses.map(c => `${c.id}`),
      getExpectedCallback: () => onCoursesChange,
    },
    {
      id: 'assignments-select',
      selection: assignments.map(a => `${a.id}`),
      getExpectedCallback: () => onAssignmentsChange,
    },
    {
      id: 'students-select',
      selection: studentsWithName.map(s => s.h_userid),
      getExpectedCallback: () => onStudentsChange,
    },
  ].forEach(({ id, selection, getExpectedCallback }) => {
    it('invokes corresponding change callback', () => {
      const wrapper = createComponent();
      const select = getSelect(wrapper, id);

      select.props().onChange(selection);
      assert.calledWith(getExpectedCallback(), selection);
    });
  });

  [true, false].forEach(isLoadingFirstPage => {
    it('shows page loading indicators when loading but not initially loading', () => {
      configureFakeAPIFetch({ isLoading: true, isLoadingFirstPage });

      const wrapper = createComponent();

      assert.equal(
        wrapper.exists('[data-testid="loading-more-courses"]'),
        !isLoadingFirstPage,
      );
      assert.equal(
        wrapper.exists('[data-testid="loading-more-assignments"]'),
        !isLoadingFirstPage,
      );
      assert.equal(
        wrapper.exists('[data-testid="loading-more-students"]'),
        !isLoadingFirstPage,
      );
    });
  });

  context('when scrolling listboxes down', () => {
    [
      {
        id: 'courses-select',
        getExpectedCallback: () => fakeLoadNextCoursesPage,
      },
      {
        id: 'assignments-select',
        getExpectedCallback: () => fakeLoadNextAssignmentsPage,
      },
      {
        id: 'students-select',
        getExpectedCallback: () => fakeLoadNextStudentsPage,
      },
    ].forEach(({ id, getExpectedCallback }) => {
      it('loads next page when scroll is at the bottom', () => {
        const wrapper = createComponent();
        const select = getSelect(wrapper, id);

        select.props().onListboxScroll({
          target: {
            scrollTop: 100,
            clientHeight: 50,
            scrollHeight: 160,
          },
        });
        assert.called(getExpectedCallback());
      });

      it('does nothing when scroll is not at the bottom', () => {
        const wrapper = createComponent();
        const select = getSelect(wrapper, id);

        select.props().onListboxScroll({
          target: {
            scrollTop: 100,
            clientHeight: 50,
            scrollHeight: 250,
          },
        });
        assert.notCalled(getExpectedCallback());
      });
    });
  });

  context('when items are selected', () => {
    [0, 1].forEach(index => {
      it('shows item name when only one is selected', () => {
        const wrapper = createComponent({
          selectedCourseIds: [`${courses[index].id}`],
          selectedAssignmentIds: [`${assignments[index].id}`],
          selectedStudentIds: [students[index].h_userid],
        });

        assert.equal(
          getSelectContent(wrapper, 'courses-select'),
          courses[index].title,
        );
        assert.equal(
          getSelectContent(wrapper, 'assignments-select'),
          assignments[index].title,
        );
        assert.equal(
          getSelectContent(wrapper, 'students-select'),
          students[index].display_name,
        );
      });
    });

    it('shows 1 selected item when a single unknown one is selected', () => {
      const wrapper = createComponent({
        selectedCourseIds: ['999'],
        selectedAssignmentIds: ['999'],
        selectedStudentIds: ['999'],
      });

      assert.equal(getSelectContent(wrapper, 'courses-select'), '1 course');
      assert.equal(
        getSelectContent(wrapper, 'assignments-select'),
        '1 assignment',
      );
      assert.equal(getSelectContent(wrapper, 'students-select'), '1 student');
    });

    it('shows amount of selected items when more than one is selected', () => {
      const wrapper = createComponent({
        selectedCourseIds: courses.map(c => `${c.id}`),
        selectedAssignmentIds: assignments.map(a => `${a.id}`),
        selectedStudentIds: studentsWithName.map(s => s.h_userid),
      });

      assert.equal(getSelectContent(wrapper, 'courses-select'), '2 courses');
      assert.equal(
        getSelectContent(wrapper, 'assignments-select'),
        '2 assignments',
      );
      assert.equal(getSelectContent(wrapper, 'students-select'), '2 students');
    });

    it('filters each dropdown by the values selected in the other dropdowns', () => {
      const selectedCourseIds = [`${courses[0].id}`];
      const selectedAssignmentIds = [`${assignments[1].id}`];
      const selectedStudentIds = studentsWithName.map(s => s.h_userid);

      createComponent({
        selectedCourseIds,
        selectedAssignmentIds,
        selectedStudentIds,
      });

      assert.calledWith(
        fakeUsePaginatedAPIFetch.getCall(0),
        'courses',
        '/api/dashboard/courses',
        {
          h_userid: selectedStudentIds,
          assignment_id: selectedAssignmentIds,
          org_public_id: undefined,
        },
      );
      assert.calledWith(
        fakeUsePaginatedAPIFetch.getCall(1),
        'assignments',
        '/api/dashboard/assignments',
        {
          h_userid: selectedStudentIds,
          course_id: selectedCourseIds,
          org_public_id: undefined,
        },
      );
      assert.calledWith(
        fakeUsePaginatedAPIFetch.getCall(2),
        'students',
        '/api/dashboard/students',
        {
          assignment_id: selectedAssignmentIds,
          course_id: selectedCourseIds,
          org_public_id: undefined,
        },
      );
    });
  });

  describe('clear filters', () => {
    [
      // Callback provided, but no items selected
      {
        props: { onClearSelection: sinon.stub() },
        shouldRenderClearButton: false,
      },
      // Callback not provided
      {
        props: {
          selectedAssignmentIds: [...assignments],
          selectedStudentIds: [...students],
        },
        shouldRenderClearButton: false,
      },
      // Callback provided and items selected
      {
        props: {
          onClearSelection: sinon.stub(),
          selectedCourseIds: [...courses],
        },
        shouldRenderClearButton: true,
      },
    ].forEach(({ props, shouldRenderClearButton }) => {
      it('shows clear button if `onClearSelection` callback was provided and some items are selected', () => {
        const wrapper = createComponent(props);
        assert.equal(
          shouldRenderClearButton,
          wrapper.exists('[data-testid="clear-button"]'),
        );
      });
    });

    it('invokes `onClearSelection` when clear button is clicked', () => {
      const onClearSelection = sinon.stub();
      const wrapper = createComponent({
        onClearSelection,
        selectedCourseIds: [...courses],
      });

      wrapper.find('button[data-testid="clear-button"]').simulate('click');

      assert.called(onClearSelection);
    });
  });

  context('when an active item is provided', () => {
    const emptySelection = {
      selectedIds: [],
      onChange: sinon.stub(),
    };
    const created = '2024-06-10T09:55:44.701550';
    const activeItem = {
      activeItem: {
        id: 123,
        title: 'The active title',
        created,
      },
      onClear: sinon.stub(),
    };

    [
      {
        props: {
          courses: activeItem,
          assignments: emptySelection,
          students: emptySelection,
        },
        selectId: 'courses-select',
        allOption: 'All courses',
        skippedAPIFetchIndex: 0,
        expectedOptionTitle: 'The active title',
      },
      {
        props: {
          courses: emptySelection,
          assignments: activeItem,
          students: emptySelection,
        },
        selectId: 'assignments-select',
        allOption: 'All assignments',
        skippedAPIFetchIndex: 1,
        expectedOptionTitle: `The active title${formatDateTime(created)}`,
      },
    ].forEach(
      ({
        props,
        selectId,
        allOption,
        skippedAPIFetchIndex,
        expectedOptionTitle,
      }) => {
        it('displays active item', () => {
          const wrapper = createComponentWithProps(props);
          const select = getSelectContent(wrapper, selectId);

          assert.equal(select, 'The active title');
        });

        it('displays only two options in select', () => {
          const wrapper = createComponentWithProps(props);
          const select = getSelect(wrapper, selectId);
          const options = select.find(MultiSelect.Option);

          assert.equal(options.length, 2);
          assert.equal(options.at(0).text(), allOption);
          assert.equal(options.at(1).text(), expectedOptionTitle);
        });

        it('does not load list of items', () => {
          createComponentWithProps(props);

          assert.calledWith(
            fakeUsePaginatedAPIFetch.getCall(skippedAPIFetchIndex),
            sinon.match.string,
            null, // The path should be null
            sinon.match.any,
          );
        });
      },
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
