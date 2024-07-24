import { MultiSelect } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
  waitFor,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import { urlPath } from '../../../utils/api';
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
      lms_id: '3',
      h_userid: 'acct:3@lms.hypothes.is',
      display_name: '', // Student with an empty name won't be displayed
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

  /**
   @param {Object} [selection]
   @param {Object[]} [selection.selectedStudents]
   @param {Object[]} [selection.selectedAssignments]
   @param {Object[]} [selection.selectedCourses]
   */
  function createComponent(selection = {}) {
    const {
      selectedStudents = [],
      selectedAssignments = [],
      selectedCourses = [],
    } = selection;

    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <DashboardActivityFilters
          selectedCourses={selectedCourses}
          onCoursesChange={onCoursesChange}
          selectedAssignments={selectedAssignments}
          onAssignmentsChange={onAssignmentsChange}
          selectedStudents={selectedStudents}
          onStudentsChange={onStudentsChange}
        />
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
      ],
    },
  ].forEach(({ id, expectedOptions }) => {
    it('renders corresponding options', () => {
      const wrapper = createComponent();
      const select = getSelect(wrapper, id);
      const options = select.find(MultiSelect.Option);

      assert.equal(options.length, expectedOptions.length);
      options.forEach((option, index) => {
        assert.equal(option.text(), expectedOptions[index]);
      });
    });
  });

  [
    {
      id: 'courses-select',
      selection: [...courses],
      getExpectedCallback: () => onCoursesChange,
      expectedQueryString: `course_id=${courses[0].id}&course_id=${courses[1].id}`,
    },
    {
      id: 'assignments-select',
      selection: [...assignments],
      getExpectedCallback: () => onAssignmentsChange,
      expectedQueryString: `assignment_id=${assignments[0].id}&assignment_id=${assignments[1].id}`,
    },
    {
      id: 'students-select',
      selection: [...studentsWithName],
      getExpectedCallback: () => onStudentsChange,
      expectedQueryString: urlPath`h_userid=${studentsWithName[0].h_userid}&h_userid=${studentsWithName[1].h_userid}`,
    },
  ].forEach(({ id, selection, getExpectedCallback, expectedQueryString }) => {
    it('invokes corresponding change callback', () => {
      const wrapper = createComponent();
      const select = getSelect(wrapper, id);

      select.props().onChange(selection);
      assert.calledWith(getExpectedCallback(), selection);

      // The query string should reflect the new selection
      assert.include(location.search, expectedQueryString);
    });
  });

  [
    {
      initialQueryString: `?course_id=${courses[0].id}&assignment_id=${assignments[0].id}`,
      expectedCourses: [courses[0]],
      expectedAssignments: [assignments[0]],
      expectedStudents: [],
    },
    {
      initialQueryString: `?course_id=${courses[0].id}&course_id=${courses[1].id}`,
      expectedCourses: [...courses],
      expectedAssignments: [],
      expectedStudents: [],
    },
    {
      initialQueryString: urlPath`?h_userid=${studentsWithName[0].h_userid}&h_userid=${studentsWithName[1].h_userid}&assignment_id=${assignments[1].id}`,
      expectedCourses: [],
      expectedAssignments: [assignments[1]],
      expectedStudents: [...studentsWithName],
    },
    {
      initialQueryString: urlPath`?h_userid=${studentsWithName[1].h_userid}`,
      expectedCourses: [],
      expectedAssignments: [],
      expectedStudents: [studentsWithName[1]],
    },
  ].forEach(
    ({
      initialQueryString,
      expectedCourses,
      expectedAssignments,
      expectedStudents,
    }) => {
      it('should initialize selection based on query string', async () => {
        history.replaceState(null, '', initialQueryString);

        createComponent();

        // Callbacks will be invoked only after corresponding courses,
        // assignments and students have been asynchronously loaded via
        // useAPIFetch, so we need to wait for it.
        await waitFor(() => onCoursesChange.called);

        assert.calledWith(onCoursesChange, expectedCourses);
        assert.calledWith(onAssignmentsChange, expectedAssignments);
        assert.calledWith(onStudentsChange, expectedStudents);
      });
    },
  );

  context('when items are selected', () => {
    [0, 1].forEach(index => {
      it('shows item name when only one is selected', () => {
        const wrapper = createComponent({
          selectedCourses: [courses[index]],
          selectedAssignments: [assignments[index]],
          selectedStudents: [students[index]],
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
        selectedCourses: [...courses],
        selectedAssignments: [...assignments],
        selectedStudents: [...studentsWithName],
      });

      assert.equal(getSelectContent(wrapper, 'courses-select'), '2 courses');
      assert.equal(
        getSelectContent(wrapper, 'assignments-select'),
        '2 assignments',
      );
      assert.equal(getSelectContent(wrapper, 'students-select'), '2 students');
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
