import { MultiSelect } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
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
    },
    {
      id: 2,
      title: 'Assignment 2',
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

  let fakeUseAPIFetch;
  let fakeConfig;
  let onCoursesChange;
  let onAssignmentsChange;
  let onStudentsChange;
  let wrappers = [];

  /**
   * @param {object} options
   * @param {boolean} options.isLoading
   */
  function configureFakeAPIFetch(fakeUseAPIFetch, options) {
    const { isLoading } = options;

    fakeUseAPIFetch.onCall(0).returns({
      isLoading,
      data: isLoading ? null : { courses },
    });
    fakeUseAPIFetch.onCall(1).returns({
      isLoading,
      data: isLoading ? null : { assignments },
    });
    fakeUseAPIFetch.onCall(2).returns({
      isLoading,
      data: isLoading ? null : { students },
    });
  }

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub();
    configureFakeAPIFetch(fakeUseAPIFetch, { isLoading: false });

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
        useAPIFetch: fakeUseAPIFetch,
      },
    });
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    $imports.$restore();
  });

  function createComponentWithProps(props) {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <DashboardActivityFilters {...props} />
      </Config.Provider>,
    );
    wrappers.push(wrapper);

    return wrapper;
  }

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
    configureFakeAPIFetch(fakeUseAPIFetch, { isLoading: true });

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
      expectedOptions: ['All assignments', ...assignments.map(a => a.title)],
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

      assert.calledWith(fakeUseAPIFetch.getCall(0), '/api/dashboard/courses', {
        h_userid: selectedStudentIds,
        assignment_id: selectedAssignmentIds,
        public_id: undefined,
      });
      assert.calledWith(
        fakeUseAPIFetch.getCall(1),
        '/api/dashboard/assignments',
        {
          h_userid: selectedStudentIds,
          course_id: selectedCourseIds,
          public_id: undefined,
        },
      );
      assert.calledWith(fakeUseAPIFetch.getCall(2), '/api/dashboard/students', {
        assignment_id: selectedAssignmentIds,
        course_id: selectedCourseIds,
        public_id: undefined,
      });
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

  const emptyFilters = {
    selectedIds: [],
    onChange: sinon.stub(),
  };

  [
    {
      props: {},
      coursesSelectShouldExist: false,
      assignmentsSelectShouldExist: false,
      studentsSelectShouldExist: false,
    },
    {
      props: { courses: emptyFilters },
      coursesSelectShouldExist: true,
      assignmentsSelectShouldExist: false,
      studentsSelectShouldExist: false,
    },
    {
      props: { assignments: emptyFilters },
      coursesSelectShouldExist: false,
      assignmentsSelectShouldExist: true,
      studentsSelectShouldExist: false,
    },
    {
      props: { assignments: emptyFilters, students: emptyFilters },
      coursesSelectShouldExist: false,
      assignmentsSelectShouldExist: true,
      studentsSelectShouldExist: true,
    },
    {
      props: {
        courses: emptyFilters,
        assignments: emptyFilters,
        students: emptyFilters,
      },
      coursesSelectShouldExist: true,
      assignmentsSelectShouldExist: true,
      studentsSelectShouldExist: true,
    },
  ].forEach(
    ({
      props,
      coursesSelectShouldExist,
      assignmentsSelectShouldExist,
      studentsSelectShouldExist,
    }) => {
      it('does not render controls for which config is not provided', () => {
        const wrapper = createComponentWithProps(props);

        assert.equal(
          wrapper.exists('[data-testid="courses-select"]'),
          coursesSelectShouldExist,
        );
        assert.equal(
          wrapper.exists('[data-testid="assignments-select"]'),
          assignmentsSelectShouldExist,
        );
        assert.equal(
          wrapper.exists('[data-testid="students-select"]'),
          studentsSelectShouldExist,
        );
      });
    },
  );

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
