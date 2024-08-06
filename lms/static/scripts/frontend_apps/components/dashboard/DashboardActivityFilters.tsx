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
  const { routes } = dashboard;

  const courses = useAPIFetch<CoursesResponse>(routes.courses, {
    h_userid: selectedStudentIds,
    assignment_id: selectedAssignmentIds,
    public_id: dashboard.organization_public_id,
  });
  const assignments = useAPIFetch<AssignmentsResponse>(routes.assignments, {
    h_userid: selectedStudentIds,
    course_id: selectedCourseIds,
    public_id: dashboard.organization_public_id,
  });
  const students = useAPIFetch<StudentsResponse>(routes.students, {
    assignment_id: selectedAssignmentIds,
    course_id: selectedCourseIds,
    public_id: dashboard.organization_public_id,
  });
  const studentsWithFallbackName: FiltersStudent[] | undefined = useMemo(
    () =>
      students.data?.students.map(({ display_name, ...s }) => ({
        ...s,
        display_name:
          display_name ??
          `Student name unavailable (ID: ${s.lms_id.substring(0, 5)})`,
        has_display_name: !!display_name,
      })),
    [students.data?.students],
  );

  return (
    <div className="flex gap-2 flex-wrap">
      <MultiSelect
        disabled={courses.isLoading}
        value={selectedCourseIds}
        onChange={onCoursesChange}
        aria-label="Select courses"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          courses.isLoading ? (
            <>...</>
          ) : selectedCourseIds.length === 0 ? (
            <>All courses</>
          ) : selectedCourseIds.length === 1 ? (
            courses.data?.courses.find(c => `${c.id}` === selectedCourseIds[0])
              ?.title
          ) : (
            <>{selectedCourseIds.length} courses</>
          )
        }
        data-testid="courses-select"
      >
        <MultiSelect.Option value={undefined}>All courses</MultiSelect.Option>
        {courses.data?.courses.map(course => (
          <MultiSelect.Option key={course.id} value={`${course.id}`}>
            {course.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={assignments.isLoading}
        value={selectedAssignmentIds}
        onChange={onAssignmentsChange}
        aria-label="Select assignments"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          assignments.isLoading ? (
            <>...</>
          ) : selectedAssignmentIds.length === 0 ? (
            <>All assignments</>
          ) : selectedAssignmentIds.length === 1 ? (
            assignments.data?.assignments.find(
              a => `${a.id}` === selectedAssignmentIds[0],
            )?.title
          ) : (
            <>{selectedAssignmentIds.length} assignments</>
          )
        }
        data-testid="assignments-select"
      >
        <MultiSelect.Option value={undefined}>
          All assignments
        </MultiSelect.Option>
        {assignments.data?.assignments.map(assignment => (
          <MultiSelect.Option key={assignment.id} value={`${assignment.id}`}>
            {assignment.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={students.isLoading}
        value={selectedStudentIds}
        onChange={onStudentsChange}
        aria-label="Select students"
        containerClasses="!w-auto min-w-[180px]"
        buttonContent={
          students.isLoading ? (
            <>...</>
          ) : selectedStudentIds.length === 0 ? (
            <>All students</>
          ) : selectedStudentIds.length === 1 ? (
            studentsWithFallbackName?.find(
              s => s.h_userid === selectedStudentIds[0],
            )?.display_name
          ) : (
            <>{selectedStudentIds.length} students</>
          )
        }
        data-testid="students-select"
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
