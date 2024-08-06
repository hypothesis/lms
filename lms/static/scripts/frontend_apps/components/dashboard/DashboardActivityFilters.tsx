import {
  CancelIcon,
  IconButton,
  MultiSelect,
} from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';

import type {
  AssignmentsResponse,
  CoursesResponse,
  Student,
  StudentsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';

export type ActivityFilters = {
  selectedIds: string[];
  onChange: (newSelectedIds: string[]) => void;
};

export type DashboardActivityFiltersProps = {
  /** Controls courses dropdown. The control will be hidden if not provided */
  courses?: ActivityFilters;
  /** Controls assignments dropdown. The control will be hidden if not provided */
  assignments?: ActivityFilters;
  /** Controls students dropdown. The control will be hidden if not provided */
  students?: ActivityFilters;

  /**
   * Invoked when clear button is clicked.
   * The button won't be shown if this is not provided.
   */
  onClearSelection?: () => void;
};

type FiltersStudent = Student & { has_display_name: boolean };

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
  const hasSelection =
    (courses && courses.selectedIds.length > 0) ||
    (assignments && assignments.selectedIds.length > 0) ||
    (students && students.selectedIds.length > 0);
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const coursesResult = useAPIFetch<CoursesResponse>(
    courses ? routes.courses : null,
    {
      h_userid: students?.selectedIds,
      assignment_id: assignments?.selectedIds,
      public_id: dashboard.organization_public_id,
    },
  );
  const assignmentsResult = useAPIFetch<AssignmentsResponse>(
    assignments ? routes.assignments : null,
    {
      h_userid: students?.selectedIds,
      course_id: courses?.selectedIds,
      public_id: dashboard.organization_public_id,
    },
  );
  const studentsResult = useAPIFetch<StudentsResponse>(
    students ? routes.students : null,
    {
      assignment_id: assignments?.selectedIds,
      course_id: courses?.selectedIds,
      public_id: dashboard.organization_public_id,
    },
  );
  const studentsWithFallbackName: FiltersStudent[] | undefined = useMemo(
    () =>
      studentsResult.data?.students.map(({ display_name, ...s }) => ({
        ...s,
        display_name:
          display_name ??
          `Student name unavailable (ID: ${s.lms_id.substring(0, 5)})`,
        has_display_name: !!display_name,
      })),
    [studentsResult.data?.students],
  );

  return (
    <div className="flex gap-2 flex-wrap">
      {courses && (
        <MultiSelect
          disabled={coursesResult.isLoading}
          value={courses.selectedIds}
          onChange={courses.onChange}
          aria-label="Select courses"
          containerClasses="!w-auto min-w-[180px]"
          buttonContent={
            coursesResult.isLoading ? (
              <>...</>
            ) : courses.selectedIds.length === 0 ? (
              <>All courses</>
            ) : courses.selectedIds.length === 1 ? (
              coursesResult.data?.courses.find(
                c => `${c.id}` === courses.selectedIds[0],
              )?.title
            ) : (
              <>{courses.selectedIds.length} courses</>
            )
          }
          data-testid="courses-select"
        >
          <MultiSelect.Option value={undefined}>All courses</MultiSelect.Option>
          {coursesResult.data?.courses.map(course => (
            <MultiSelect.Option key={course.id} value={`${course.id}`}>
              {course.title}
            </MultiSelect.Option>
          ))}
        </MultiSelect>
      )}
      {assignments && (
        <MultiSelect
          disabled={assignmentsResult.isLoading}
          value={assignments.selectedIds}
          onChange={assignments.onChange}
          aria-label="Select assignments"
          containerClasses="!w-auto min-w-[180px]"
          buttonContent={
            assignmentsResult.isLoading ? (
              <>...</>
            ) : assignments.selectedIds.length === 0 ? (
              <>All assignments</>
            ) : assignments.selectedIds.length === 1 ? (
              assignmentsResult.data?.assignments.find(
                a => `${a.id}` === assignments.selectedIds[0],
              )?.title
            ) : (
              <>{assignments.selectedIds.length} assignments</>
            )
          }
          data-testid="assignments-select"
        >
          <MultiSelect.Option value={undefined}>
            All assignments
          </MultiSelect.Option>
          {assignmentsResult.data?.assignments.map(assignment => (
            <MultiSelect.Option key={assignment.id} value={`${assignment.id}`}>
              {assignment.title}
            </MultiSelect.Option>
          ))}
        </MultiSelect>
      )}
      {students && (
        <MultiSelect
          disabled={studentsResult.isLoading}
          value={students.selectedIds}
          onChange={students.onChange}
          aria-label="Select students"
          containerClasses="!w-auto min-w-[180px]"
          buttonContent={
            studentsResult.isLoading ? (
              <>...</>
            ) : students.selectedIds.length === 0 ? (
              <>All students</>
            ) : students.selectedIds.length === 1 ? (
              studentsWithFallbackName?.find(
                s => s.h_userid === students.selectedIds[0],
              )?.display_name
            ) : (
              <>{students.selectedIds.length} students</>
            )
          }
          data-testid="students-select"
        >
          <MultiSelect.Option value={undefined}>
            All students
          </MultiSelect.Option>
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
        </MultiSelect>
      )}
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
