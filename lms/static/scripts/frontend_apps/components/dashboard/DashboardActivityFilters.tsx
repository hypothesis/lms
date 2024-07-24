import { MultiSelect } from '@hypothesis/frontend-shared';
import { useCallback, useEffect, useMemo } from 'preact/hooks';
import { useLocation, useSearch } from 'wouter-preact';

import type { Assignment, Course, Student } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import {
  queryStringToRecord,
  recordToQueryStringFragment,
} from '../../utils/url';

export type DashboardActivityFiltersProps = {
  selectedCourses: Course[];
  onCoursesChange: (newCourses: Course[]) => void;
  selectedAssignments: Assignment[];
  onAssignmentsChange: (newAssignments: Assignment[]) => void;
  selectedStudents: Student[];
  onStudentsChange: (newStudents: Student[]) => void;
};

/**
 * Renders drop-downs to select courses, assignments and/or students, used to
 * filter dashboard activity metrics.
 */
export default function DashboardActivityFilters({
  selectedCourses,
  onCoursesChange,
  selectedAssignments,
  onAssignmentsChange,
  selectedStudents,
  onStudentsChange,
}: DashboardActivityFiltersProps) {
  const search = useSearch();
  const queryParams = useMemo(() => queryStringToRecord(search), [search]);
  const [, navigate] = useLocation();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  /**
   * Used to persist selected filters in the query string
   */
  const updateQueryString = useCallback(
    (paramsToUpdate: Record<string, string[]>) => {
      const newQueryParams = { ...queryParams, ...paramsToUpdate };
      navigate(recordToQueryStringFragment(newQueryParams));
    },
    [navigate, queryParams],
  );

  const courses = useAPIFetch<{ courses: Course[] }>(routes.courses);
  const assignments = useAPIFetch<{ assignments: Assignment[] }>(
    routes.assignments,
  );
  const students = useAPIFetch<{ students: Student[] }>(routes.students);
  const studentsWithName = useMemo(
    () => students.data?.students.filter(s => !!s.display_name),
    [students.data?.students],
  );

  // Try to initialize selection based on query parameters
  useEffect(() => {
    const { course_id = [] } = queryParams;
    const courseIds = Array.isArray(course_id) ? course_id : [course_id];

    if (courses.data) {
      onCoursesChange(
        courses.data.courses.filter(c => courseIds.includes(`${c.id}`)),
      );
    }
  }, [courses.data, onCoursesChange, queryParams]);
  useEffect(() => {
    const { assignment_id = [] } = queryParams;
    const assignmentIds = Array.isArray(assignment_id)
      ? assignment_id
      : [assignment_id];

    if (assignments.data) {
      onAssignmentsChange(
        assignments.data.assignments.filter(a =>
          assignmentIds.includes(`${a.id}`),
        ),
      );
    }
  }, [assignments.data, onAssignmentsChange, queryParams]);
  useEffect(() => {
    const { h_userid = [] } = queryParams;
    const studentIds = Array.isArray(h_userid) ? h_userid : [h_userid];

    if (students.data) {
      onStudentsChange(
        students.data.students.filter(s => studentIds.includes(s.h_userid)),
      );
    }
  }, [onStudentsChange, queryParams, students.data]);

  return (
    <div className="flex gap-2 md:w-1/2">
      <MultiSelect
        disabled={courses.isLoading}
        value={selectedCourses}
        onChange={newCourses => {
          updateQueryString({ course_id: newCourses.map(c => `${c.id}`) });
          onCoursesChange(newCourses);
        }}
        aria-label="Select courses"
        buttonContent={
          courses.isLoading ? (
            <>...</>
          ) : selectedCourses.length === 0 ? (
            <>All courses</>
          ) : selectedCourses.length === 1 ? (
            selectedCourses[0].title
          ) : (
            <>{selectedCourses.length} courses</>
          )
        }
        data-testid="courses-select"
      >
        <MultiSelect.Option value={undefined}>All courses</MultiSelect.Option>
        {courses.data?.courses.map(course => (
          <MultiSelect.Option key={course.id} value={course}>
            {course.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={assignments.isLoading}
        value={selectedAssignments}
        onChange={newAssignments => {
          updateQueryString({
            assignment_id: newAssignments.map(a => `${a.id}`),
          });
          onAssignmentsChange(newAssignments);
        }}
        aria-label="Select assignments"
        buttonContent={
          assignments.isLoading ? (
            <>...</>
          ) : selectedAssignments.length === 0 ? (
            <>All assignments</>
          ) : selectedAssignments.length === 1 ? (
            selectedAssignments[0].title
          ) : (
            <>{selectedAssignments.length} assignments</>
          )
        }
        data-testid="assignments-select"
      >
        <MultiSelect.Option value={undefined}>
          All assignments
        </MultiSelect.Option>
        {assignments.data?.assignments.map(assignment => (
          <MultiSelect.Option key={assignment.id} value={assignment}>
            {assignment.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={students.isLoading}
        value={selectedStudents}
        onChange={newStudents => {
          updateQueryString({ h_userid: newStudents.map(s => s.h_userid) });
          onStudentsChange(newStudents);
        }}
        aria-label="Select students"
        buttonContent={
          students.isLoading ? (
            <>...</>
          ) : selectedStudents.length === 0 ? (
            <>All students</>
          ) : selectedStudents.length === 1 ? (
            selectedStudents[0].display_name
          ) : (
            <>{selectedStudents.length} students</>
          )
        }
        data-testid="students-select"
      >
        <MultiSelect.Option value={undefined}>All students</MultiSelect.Option>
        {studentsWithName?.map(student => (
          <MultiSelect.Option key={student.lms_id} value={student}>
            {student.display_name}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
    </div>
  );
}
