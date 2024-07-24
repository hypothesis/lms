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
   @param {Object[]} [selection.selectedStudentIds]
   @param {Object[]} [selection.selectedAssignmentIds]
   @param {Object[]} [selection.selectedCourseIds]
   */
  function createComponent(selection = {}) {
    const {
      selectedStudentIds = [],
      selectedAssignmentIds = [],
      selectedCourseIds = [],
    } = selection;

    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <DashboardActivityFilters
          selectedCourseIds={selectedCourseIds}
          onCoursesChange={onCoursesChange}
          selectedAssignmentIds={selectedAssignmentIds}
          onAssignmentsChange={onAssignmentsChange}
          selectedStudentIds={selectedStudentIds}
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
        selectedCourseIds: [...courses],
        selectedAssignmentIds: [...assignments],
        selectedStudentIds: [...studentsWithName],
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
