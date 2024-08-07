import {
  CancelIcon,
  IconButton,
  MultiSelect,
} from '@hypothesis/frontend-shared';
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
  selectedIds: string[];
  onChange: (newSelectedIds: string[]) => void;
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

  const [selectedCourseIds, activeCourse] = useMemo(() => {
    const isSelection = 'selectedIds' in courses;

    return isSelection
      ? [courses.selectedIds, null]
      : [[`${courses.activeItem.id}`], courses.activeItem];
  }, [courses]);
  const [selectedAssignmentIds, activeAssignment] = useMemo(() => {
    const isSelection = 'selectedIds' in assignments;
    return isSelection
      ? [assignments.selectedIds, null]
      : [[`${assignments.activeItem.id}`], assignments.activeItem];
  }, [assignments]);

  const hasSelection =
    students.selectedIds.length > 0 ||
    selectedAssignmentIds.length > 0 ||
    selectedCourseIds.length > 0;

  const coursesFilters = useMemo(
    () => ({
      h_userid: students.selectedIds,
      assignment_id: selectedAssignmentIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentIds, students.selectedIds],
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
      h_userid: students.selectedIds,
      course_id: selectedCourseIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedCourseIds, students.selectedIds],
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
      assignment_id: selectedAssignmentIds,
      course_id: selectedCourseIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentIds, selectedCourseIds],
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
      <MultiSelect
        disabled={coursesResult.isLoadingFirstPage}
        value={selectedCourseIds}
        onChange={newCourseIds =>
          'onChange' in courses
            ? courses.onChange(newCourseIds)
            : courses.onClear()
        }
        aria-label="Select courses"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          activeCourse ? (
            activeCourse.title
          ) : coursesResult.isLoadingFirstPage ? (
            <>...</>
          ) : selectedCourseIds.length === 0 ? (
            <>All courses</>
          ) : selectedCourseIds.length === 1 ? (
            coursesResult.data?.find(c => `${c.id}` === selectedCourseIds[0])
              ?.title ?? '1 course'
          ) : (
            <>{selectedCourseIds.length} courses</>
          )
        }
        data-testid="courses-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            coursesResult.loadNextPage();
          }
        }}
      >
        <MultiSelect.Option value={undefined}>All courses</MultiSelect.Option>
        {activeCourse ? (
          <MultiSelect.Option
            key={activeCourse.id}
            value={`${activeCourse.id}`}
          >
            {activeCourse.title}
          </MultiSelect.Option>
        ) : (
          <>
            {coursesResult.data?.map(course => (
              <MultiSelect.Option key={course.id} value={`${course.id}`}>
                {course.title}
              </MultiSelect.Option>
            ))}
            {coursesResult.isLoading && !coursesResult.isLoadingFirstPage && (
              <MultiSelect.Option disabled value={undefined}>
                <span className="italic" data-testid="loading-more-courses">
                  Loading more courses...
                </span>
              </MultiSelect.Option>
            )}
          </>
        )}
      </MultiSelect>
      <MultiSelect
        disabled={assignmentsResults.isLoadingFirstPage}
        value={selectedAssignmentIds}
        onChange={newAssignmentIds =>
          'onChange' in assignments
            ? assignments.onChange(newAssignmentIds)
            : assignments.onClear()
        }
        aria-label="Select assignments"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          activeAssignment ? (
            activeAssignment.title
          ) : assignmentsResults.isLoadingFirstPage ? (
            <>...</>
          ) : selectedAssignmentIds.length === 0 ? (
            <>All assignments</>
          ) : selectedAssignmentIds.length === 1 ? (
            assignmentsResults.data?.find(
              a => `${a.id}` === selectedAssignmentIds[0],
            )?.title ?? '1 assignment'
          ) : (
            <>{selectedAssignmentIds.length} assignments</>
          )
        }
        data-testid="assignments-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            assignmentsResults.loadNextPage();
          }
        }}
      >
        <MultiSelect.Option value={undefined}>
          All assignments
        </MultiSelect.Option>
        {activeAssignment ? (
          <MultiSelect.Option
            key={activeAssignment.id}
            value={`${activeAssignment.id}`}
          >
            {activeAssignment.title}
          </MultiSelect.Option>
        ) : (
          <>
            {assignmentsResults.data?.map(assignment => (
              <MultiSelect.Option
                key={assignment.id}
                value={`${assignment.id}`}
              >
                {assignment.title}
              </MultiSelect.Option>
            ))}
            {assignmentsResults.isLoading &&
              !assignmentsResults.isLoadingFirstPage && (
                <MultiSelect.Option disabled value={undefined}>
                  <span
                    className="italic"
                    data-testid="loading-more-assignments"
                  >
                    Loading more assignments...
                  </span>
                </MultiSelect.Option>
              )}
          </>
        )}
      </MultiSelect>
      <MultiSelect
        disabled={studentsResult.isLoadingFirstPage}
        value={students.selectedIds}
        onChange={students.onChange}
        aria-label="Select students"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          studentsResult.isLoadingFirstPage ? (
            <>...</>
          ) : students.selectedIds.length === 0 ? (
            <>All students</>
          ) : students.selectedIds.length === 1 ? (
            studentsWithFallbackName?.find(
              s => s.h_userid === students.selectedIds[0],
            )?.display_name ?? '1 student'
          ) : (
            <>{students.selectedIds.length} students</>
          )
        }
        data-testid="students-select"
        onListboxScroll={e => {
          if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
            studentsResult.loadNextPage();
          }
        }}
      >
        <MultiSelect.Option value={undefined}>All students</MultiSelect.Option>
        {studentsWithFallbackName?.map(student => (
          <MultiSelect.Option key={student.lms_id} value={student.h_userid}>
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
          </MultiSelect.Option>
        ))}
        {studentsResult.isLoading && !studentsResult.isLoadingFirstPage && (
          <MultiSelect.Option disabled value={undefined}>
            <span className="italic" data-testid="loading-more-students">
              Loading more students...
            </span>
          </MultiSelect.Option>
        )}
      </MultiSelect>
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
