import { MultiSelect } from '@hypothesis/frontend-shared';
import { formatDateTime } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
  mount,
} from '@hypothesis/frontend-testing';
import sinon from 'sinon';

import { Config } from '../../../config';
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

  /**
   * @param {object} options
   * @param {boolean} options.isLoading
   * @param {boolean} [options.isLoadingFirstPage] - Defaults to isLoading
   * @param {Error} [options.error] - Defaults to null
   * @param {() => void} [options.retry] - Defaults to noop
   */
  function configureFakeAPIFetch(options) {
    const {
      isLoading,
      isLoadingFirstPage = isLoading,
      error = null,
      retry = () => {},
    } = options;

    fakeUsePaginatedAPIFetch.onCall(0).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading || error ? null : courses,
      loadNextPage: fakeLoadNextCoursesPage,
      error,
      retry,
    });
    fakeUsePaginatedAPIFetch.onCall(1).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading || error ? null : assignments,
      loadNextPage: fakeLoadNextAssignmentsPage,
      error,
      retry,
    });
    fakeUsePaginatedAPIFetch.onCall(2).returns({
      isLoading,
      isLoadingFirstPage,
      data: isLoading || error ? null : students,
      loadNextPage: fakeLoadNextStudentsPage,
      error,
      retry,
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
    // Do not mock ContentWithBadge, as it helps test scenarios where it is
    // used vs scenarios where it isn't
    $imports.$restore({
      './ContentWithBadge': true,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  /**
   *
   * @param {object} options
   * @param {string[] | undefined} [options.selectedCourseIds]
   * @param {string[] | undefined} [options.selectedAssignmentIds]
   * @param {string[] | undefined} [options.selectedStudentIds]
   * @param {object | undefined} [options.segments]
   * @param {(...args: unknown[]) => unknown | undefined} [options.onClearSelection]
   */
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
      segments: options.segments,
      onClearSelection: options.onClearSelection,
    });
  }

  function createComponentWithProps(props) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <DashboardActivityFilters {...props} />
      </Config.Provider>,
      { connected: true },
    );
  }

  function getSelect(wrapper, id) {
    return wrapper.find(`PaginatedMultiSelect[data-testid="${id}"]`);
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

  it('shows placeholders with count when selection is empty', () => {
    const wrapper = createComponent();

    assert.equal(
      getSelectContent(wrapper, 'courses-select'),
      `All courses${courses.length}`,
    );
    assert.equal(
      getSelectContent(wrapper, 'assignments-select'),
      `All assignments${assignments.length}`,
    );
    assert.equal(
      getSelectContent(wrapper, 'students-select'),
      `All students${students.length}`,
    );
  });

  [
    // Course
    {
      id: 'courses-select',
      entity: courses[0],
      expectedText: courses[0].title,
    },
    // Assignment
    {
      id: 'assignments-select',
      entity: assignments[0],
      expectedText: `${assignments[0].title}${formatDateTime(assignments[0].created)}`,
    },
    // Student with name
    {
      id: 'students-select',
      entity: students[0],
      expectedText: students[0].display_name,
    },
    // Student without name
    {
      id: 'students-select',
      entity: students[students.length - 1],
      expectedText: 'Student name unavailable (ID: 12345)',
      expectedTitle: 'User ID: 123456789',
    },
  ].forEach(({ id, entity, expectedText, expectedTitle }) => {
    it('formats select options', () => {
      const wrapper = createComponent();
      const select = getSelect(wrapper, id);

      // The option needs to be wrapped in a select, otherwise it throws.
      const tempSelect = mount(
        <MultiSelect value={[]} onChange={sinon.stub()}>
          {select.props().renderOption(entity)}
        </MultiSelect>,
        { connected: true },
      );
      // The Select needs to be open, otherwise options are not rendered
      tempSelect.find('button').simulate('click');
      const option = tempSelect.find(MultiSelect.Option);

      try {
        assert.equal(option.text(), expectedText);

        if (expectedTitle) {
          assert.equal(
            option.find('[data-testid="option-content-wrapper"]').prop('title'),
            expectedTitle,
          );
        }
      } finally {
        // We need to unmount the temp select, to avoid a disconnected popover
        // to be left in the DOM and affect other tests
        tempSelect.unmount();
      }
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
          segment_authority_provided_id: [],
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
        skippedAPIFetchIndex: 0,
      },
      {
        props: {
          courses: emptySelection,
          assignments: activeItem,
          students: emptySelection,
        },
        selectId: 'assignments-select',
        skippedAPIFetchIndex: 1,
      },
    ].forEach(({ props, selectId, skippedAPIFetchIndex }) => {
      it('displays active item', () => {
        const wrapper = createComponentWithProps(props);
        const select = getSelectContent(wrapper, selectId);

        assert.equal(select, 'The active title');
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
    });
  });

  context('when segments are provided', () => {
    let onSegmentsChange;

    beforeEach(() => {
      onSegmentsChange = sinon.stub();
    });

    function createComponentWithSegments(segmentsConfig = {}) {
      return createComponent({
        segments: {
          selectedIds: [],
          entries: [],
          type: 'groups',
          onChange: onSegmentsChange,
          ...segmentsConfig,
        },
      });
    }

    function getSegmentsSelect(wrapper) {
      return wrapper.find('[data-testid="segments-select"]');
    }

    function getOpenSegmentsSelect(wrapper) {
      const select = getSegmentsSelect(wrapper);
      select.find('button').simulate('click');
      const options = wrapper.find('[role="option"]');

      return { select, options };
    }

    [true, false].forEach(withSegments => {
      it('shows an extra multi-select for segments', () => {
        const wrapper = withSegments
          ? createComponentWithSegments()
          : createComponent();

        assert.equal(getSegmentsSelect(wrapper).exists(), withSegments);
      });
    });

    it('sets initially selected values', () => {
      const selectedIds = ['bar', 'baz'];
      const wrapper = createComponentWithSegments({ selectedIds });
      const select = getSegmentsSelect(wrapper);

      assert.deepEqual(select.prop('value'), selectedIds);
    });

    [
      { entries: [], shouldBeDisabled: true },
      { entries: ['foo', 'bar'], shouldBeDisabled: false },
    ].forEach(({ entries, shouldBeDisabled }) => {
      it('disables segments filter when entries are empty', () => {
        const wrapper = createComponentWithSegments({ entries });
        assert.equal(
          getSegmentsSelect(wrapper).prop('disabled'),
          shouldBeDisabled,
        );
      });
    });

    it('invokes onChange callback', () => {
      const wrapper = createComponentWithSegments();
      const select = getSegmentsSelect(wrapper);

      select.props().onChange(['foo', 'bar']);

      assert.calledWith(onSegmentsChange, ['foo', 'bar']);
    });

    ['groups', 'sections'].forEach(type => {
      it('sets label based on segment type', () => {
        const wrapper = createComponentWithSegments({ type });
        const select = getSegmentsSelect(wrapper);

        assert.equal(select.prop('aria-label'), `Select ${type}`);
      });
    });

    [
      // No selection for groups
      {
        segmentsConfig: { type: 'groups' },
        expectedButtonContent: 'All groups0',
      },
      // No selection for sections
      {
        segmentsConfig: { type: 'sections' },
        expectedButtonContent: 'All sections0',
      },
      // "None" type
      {
        segmentsConfig: { type: 'none' },
        expectedButtonContent: 'No sections/groups',
      },
      // 1 known selected item
      {
        segmentsConfig: {
          entries: [
            {
              h_authority_provided_id: '1',
              name: 'Selected Name',
            },
          ],
          selectedIds: ['1'],
        },
        expectedButtonContent: 'Selected Name',
      },
      // 1 unknown selected group
      {
        segmentsConfig: {
          type: 'groups',
          entries: [
            {
              h_authority_provided_id: '1',
              name: 'Selected Name',
            },
          ],
          selectedIds: ['3'],
        },
        expectedButtonContent: '1 group',
      },
      // 1 unknown selected section
      {
        segmentsConfig: {
          type: 'sections',
          entries: [
            {
              h_authority_provided_id: '1',
              name: 'Selected Name',
            },
          ],
          selectedIds: ['3'],
        },
        expectedButtonContent: '1 section',
      },
      // Multiple selected groups
      {
        segmentsConfig: {
          type: 'groups',
          selectedIds: ['1', '3', '8'],
        },
        expectedButtonContent: '3 groups',
      },
      // Multiple selected sections
      {
        segmentsConfig: {
          type: 'sections',
          selectedIds: ['1', '3'],
        },
        expectedButtonContent: '2 sections',
      },
    ].forEach(({ expectedButtonContent, segmentsConfig }) => {
      it('shows expected segments button content', () => {
        const wrapper = createComponentWithSegments(segmentsConfig);
        const content = mount(
          <div>{getSegmentsSelect(wrapper).prop('buttonContent')}</div>,
        );

        try {
          assert.equal(content.text(), expectedButtonContent);
        } finally {
          content.unmount();
        }
      });
    });

    [{ entries: [] }, { entries: [{}, {}, {}] }, { entries: [{}] }].forEach(
      ({ entries }) => {
        it('shows expected number of options', () => {
          const wrapper = createComponentWithSegments({ entries });
          const { options } = getOpenSegmentsSelect(wrapper);

          assert.equal(options.length, entries.length + 1);
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
