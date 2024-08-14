import { CancelIcon, IconButton, Select } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type {
  Assignment,
  AssignmentsResponse,
  Course,
  CoursesResponse,
  Student,
  StudentsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { usePaginatedAPIFetch } from '../../utils/api';

/**
 * Allow the user to select items from a paginated list of all items matching
 * the current filters.
 * The set of currently selected items are maintained by the parent component.
 */
export type ActivityFilterSelection = {
  selectedId: string | undefined;
  onChange: (newSelectedId: string | undefined) => void;
};

/**
 * Display two items in the dropdown, one for an active / selected item and one
 * to clear the selection.
 */
export type ActivityFilterItem<T extends Course | Assignment> = {
  activeItem: T;
  onClear: () => void;
};

export type DashboardActivityFiltersProps = {
  courses: ActivityFilterSelection | ActivityFilterItem<Course>;
  assignments: ActivityFilterSelection | ActivityFilterItem<Assignment>;
  students: ActivityFilterSelection;
  onClearSelection?: () => void;
};

type FiltersStudent = Student & { has_display_name: boolean };

/**
 * Checks if provided element's scroll is at the bottom.
 * @param offset - Return true if the difference between the element's current
 *                 and maximum scroll position is below this value.
 *                 Defaults to 20.
 */
function elementScrollIsAtBottom(element: HTMLElement, offset = 20): boolean {
  const distanceToTop = element.scrollTop + element.clientHeight;
  const triggerPoint = element.scrollHeight - offset;
  return distanceToTop >= triggerPoint;
}

/**
 * Renders drop-downs to select courses, assignments and/or students, used to
 * filter dashboard activity metrics.
 */
export default function DashboardActivityFilters({
  courses,
  assignments,
  students,
  onClearSelection,
}: DashboardActivityFiltersProps) {
  const { dashboard } = useConfig(['dashboard']);
  const { organizationPublicId } = useParams();
  const { routes } = dashboard;

  const [selectedCourseId, activeCourse] = useMemo(() => {
    const isSelection = 'selectedId' in courses;

    return isSelection
      ? [courses.selectedId, null]
      : [`${courses.activeItem.id}`, courses.activeItem];
  }, [courses]);
  const [selectedAssignmentId, activeAssignment] = useMemo(() => {
    const isSelection = 'selectedId' in assignments;
    return isSelection
      ? [assignments.selectedId, null]
      : [`${assignments.activeItem.id}`, assignments.activeItem];
  }, [assignments]);

  const hasSelection =
    !!students.selectedId || !!selectedAssignmentId || !!selectedCourseId;

  const coursesFilters = useMemo(
    () => ({
      h_userid: students.selectedId,
      assignment_id: selectedAssignmentId,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentId, students.selectedId],
  );
  const coursesResult = usePaginatedAPIFetch<
    'courses',
    Course[],
    CoursesResponse
  >(
    'courses',
    // If an active course was provided, do not load list of courses
    activeCourse ? null : routes.courses,
    coursesFilters,
  );

  const assignmentFilters = useMemo(
    () => ({
      h_userid: students.selectedId,
      course_id: selectedCourseId,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedCourseId, students.selectedId],
  );
  const assignmentsResults = usePaginatedAPIFetch<
    'assignments',
    Assignment[],
    AssignmentsResponse
  >(
    'assignments',
    // If an active assignment was provided, do not load list of assignments
    activeAssignment ? null : routes.assignments,
    assignmentFilters,
  );

  const studentsFilters = useMemo(
    () => ({
      assignment_id: selectedAssignmentId,
      course_id: selectedCourseId,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentId, selectedCourseId],
  );
  const studentsResult = usePaginatedAPIFetch<
    'students',
    Student[],
    StudentsResponse
  >('students', routes.students, studentsFilters);
  const studentsWithFallbackName: FiltersStudent[] | undefined = useMemo(
    () =>
      studentsResult.data?.map(({ display_name, ...s }) => ({
        ...s,
        display_name:
          display_name ??
          `Student name unavailable (ID: ${s.lms_id.substring(0, 5)})`,
        has_display_name: !!display_name,
      })),
    [studentsResult.data],
  );

  return (
    <div className="flex gap-2 flex-wrap">
      <Select
        disabled={coursesResult.isLoadingFirstPage}
        value={selectedCourseId}
        onChange={newCourseId =>
          'onChange' in courses
            ? courses.onChange(newCourseId)
            : courses.onClear()
        }
        aria-label="Select courses"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          activeCourse ? (
            activeCourse.title
          ) : coursesResult.isLoadingFirstPage ? (
            <>...</>
          ) : !selectedCourseId ? (
            <>All courses</>
          ) : (
            coursesResult.data?.find(c => `${c.id}` === selectedCourseId[0])
              ?.title ?? '1 course'
          )
        }
        data-testid="courses-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            coursesResult.loadNextPage();
          }
        }}
      >
        <Select.Option value={undefined}>All courses</Select.Option>
        {activeCourse ? (
          <Select.Option key={activeCourse.id} value={`${activeCourse.id}`}>
            {activeCourse.title}
          </Select.Option>
        ) : (
          <>
            {coursesResult.data?.map(course => (
              <Select.Option key={course.id} value={`${course.id}`}>
                {course.title}
              </Select.Option>
            ))}
            {coursesResult.isLoading && !coursesResult.isLoadingFirstPage && (
              <Select.Option disabled value={undefined}>
                <span className="italic" data-testid="loading-more-courses">
                  Loading more courses...
                </span>
              </Select.Option>
            )}
          </>
        )}
      </Select>
      <Select
        disabled={assignmentsResults.isLoadingFirstPage}
        value={selectedAssignmentId}
        onChange={newAssignmentId =>
          'onChange' in assignments
            ? assignments.onChange(newAssignmentId)
            : assignments.onClear()
        }
        aria-label="Select assignments"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          activeAssignment ? (
            activeAssignment.title
          ) : assignmentsResults.isLoadingFirstPage ? (
            <>...</>
          ) : !selectedAssignmentId ? (
            <>All assignments</>
          ) : (
            assignmentsResults.data?.find(
              a => `${a.id}` === selectedAssignmentId,
            )?.title ?? '1 assignment'
          )
        }
        data-testid="assignments-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            assignmentsResults.loadNextPage();
          }
        }}
      >
        <Select.Option value={undefined}>All assignments</Select.Option>
        {activeAssignment ? (
          <Select.Option
            key={activeAssignment.id}
            value={`${activeAssignment.id}`}
          >
            {activeAssignment.title}
          </Select.Option>
        ) : (
          <>
            {assignmentsResults.data?.map(assignment => (
              <Select.Option key={assignment.id} value={`${assignment.id}`}>
                {assignment.title}
              </Select.Option>
            ))}
            {assignmentsResults.isLoading &&
              !assignmentsResults.isLoadingFirstPage && (
                <Select.Option disabled value={undefined}>
                  <span
                    className="italic"
                    data-testid="loading-more-assignments"
                  >
                    Loading more assignments...
                  </span>
                </Select.Option>
              )}
          </>
        )}
      </Select>
      <Select
        disabled={studentsResult.isLoadingFirstPage}
        value={students.selectedId}
        onChange={newStudentId => students.onChange(newStudentId)}
        aria-label="Select students"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          studentsResult.isLoadingFirstPage ? (
            <>...</>
          ) : !students.selectedId ? (
            <>All students</>
          ) : (
            studentsWithFallbackName?.find(
              s => s.h_userid === students.selectedId,
            )?.display_name ?? '1 student'
          )
        }
        data-testid="students-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            studentsResult.loadNextPage();
          }
        }}
      >
        <Select.Option value={undefined}>All students</Select.Option>
        {studentsWithFallbackName?.map(student => (
          <Select.Option key={student.lms_id} value={student.h_userid}>
            <span
              className={student.has_display_name ? undefined : 'italic'}
              title={
                student.has_display_name
                  ? undefined
                  : `User ID: ${student.lms_id}`
              }
              data-testid="option-content-wrapper"
            >
              {student.display_name}
            </span>
          </Select.Option>
        ))}
        {studentsResult.isLoading && !studentsResult.isLoadingFirstPage && (
          <Select.Option disabled value={undefined}>
            <span className="italic" data-testid="loading-more-students">
              Loading more students...
            </span>
          </Select.Option>
        )}
      </Select>
      {hasSelection && onClearSelection && (
        <IconButton
          title="Clear filters"
          icon={CancelIcon}
          classes="text-grey-7"
          onClick={() => onClearSelection()}
          data-testid="clear-button"
        />
      )}
    </div>
  );
}
