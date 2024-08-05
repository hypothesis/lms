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

export type DashboardActivityFiltersProps = {
  selectedCourseIds: string[];
  onCoursesChange: (newCourseIds: string[]) => void;
  selectedAssignmentIds: string[];
  onAssignmentsChange: (newAssignmentIds: string[]) => void;
  selectedStudentIds: string[];
  onStudentsChange: (newStudentIds: string[]) => void;
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
  selectedCourseIds,
  onCoursesChange,
  selectedAssignmentIds,
  onAssignmentsChange,
  selectedStudentIds,
  onStudentsChange,
  onClearSelection,
}: DashboardActivityFiltersProps) {
  const hasSelection =
    selectedStudentIds.length > 0 ||
    selectedAssignmentIds.length > 0 ||
    selectedCourseIds.length > 0;
  const { dashboard } = useConfig(['dashboard']);
  const { organizationPublicId } = useParams();
  const { routes } = dashboard;

  const coursesFilters = useMemo(
    () => ({
      h_userid: selectedStudentIds,
      assignment_id: selectedAssignmentIds,
      public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentIds, selectedStudentIds],
  );
  const coursesResult = usePaginatedAPIFetch<
    'courses',
    Course[],
    CoursesResponse
  >('courses', routes.courses, coursesFilters);

  const assignmentFilters = useMemo(
    () => ({
      h_userid: selectedStudentIds,
      course_id: selectedCourseIds,
      public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedCourseIds, selectedStudentIds],
  );
  const assignmentsResults = usePaginatedAPIFetch<
    'assignments',
    Assignment[],
    AssignmentsResponse
  >('assignments', routes.assignments, assignmentFilters);

  const studentsFilters = useMemo(
    () => ({
      assignment_id: selectedAssignmentIds,
      course_id: selectedCourseIds,
      public_id: organizationPublicId,
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
        onChange={onCoursesChange}
        aria-label="Select courses"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          coursesResult.isLoadingFirstPage ? (
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
      </MultiSelect>
      <MultiSelect
        disabled={assignmentsResults.isLoadingFirstPage}
        value={selectedAssignmentIds}
        onChange={onAssignmentsChange}
        aria-label="Select assignments"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          assignmentsResults.isLoadingFirstPage ? (
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
        {assignmentsResults.data?.map(assignment => (
          <MultiSelect.Option key={assignment.id} value={`${assignment.id}`}>
            {assignment.title}
          </MultiSelect.Option>
        ))}
        {assignmentsResults.isLoading &&
          !assignmentsResults.isLoadingFirstPage && (
            <MultiSelect.Option disabled value={undefined}>
              <span className="italic" data-testid="loading-more-assignments">
                Loading more assignments...
              </span>
            </MultiSelect.Option>
          )}
      </MultiSelect>
      <MultiSelect
        disabled={studentsResult.isLoadingFirstPage}
        value={selectedStudentIds}
        onChange={onStudentsChange}
        aria-label="Select students"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          studentsResult.isLoadingFirstPage ? (
            <>...</>
          ) : selectedStudentIds.length === 0 ? (
            <>All students</>
          ) : selectedStudentIds.length === 1 ? (
            studentsWithFallbackName?.find(
              s => s.h_userid === selectedStudentIds[0],
            )?.display_name ?? '1 student'
          ) : (
            <>{selectedStudentIds.length} students</>
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
