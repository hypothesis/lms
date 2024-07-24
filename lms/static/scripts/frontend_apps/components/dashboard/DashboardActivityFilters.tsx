import { MultiSelect } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';

import type { Assignment, Course, Student } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';

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
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const courses = useAPIFetch<{ courses: Course[] }>(routes.courses);
  const assignments = useAPIFetch<{ assignments: Assignment[] }>(
    routes.assignments,
  );
  const students = useAPIFetch<{ students: Student[] }>(routes.students);
  const studentsWithName = useMemo(
    () => students.data?.students.filter(s => !!s.display_name),
    [students.data?.students],
  );

  return (
    <div className="flex gap-2 md:w-1/2">
      <MultiSelect
        disabled={courses.isLoading}
        value={selectedCourses}
        onChange={onCoursesChange}
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
        onChange={onAssignmentsChange}
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
        onChange={onStudentsChange}
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