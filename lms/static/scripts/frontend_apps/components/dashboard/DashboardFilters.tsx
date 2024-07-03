import { MultiSelect } from '@hypothesis/frontend-shared';

import type { Assignment, Course, Student } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';

export type DashboardFiltersProps = {
  selectedCourses?: Course[];
  onCoursesChange?: (newCourses: Course[]) => void;
  selectedAssignments?: Assignment[];
  onAssignmentsChange?: (newAssignments: Assignment[]) => void;
  selectedStudents?: Student[];
  onStudentsChange?: (newStudents: Student[]) => void;
};

const noop = () => {};

export default function DashboardFilters({
  selectedCourses = [],
  onCoursesChange = noop,
  selectedAssignments = [],
  onAssignmentsChange = noop,
  selectedStudents = [],
  onStudentsChange = noop,
}: DashboardFiltersProps) {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const courses = useAPIFetch<{ courses: Course[] }>(routes.courses);
  const assignments = useAPIFetch<{ assignments: Assignment[] }>(
    routes.assignments,
  );
  const students = useAPIFetch<{ students: Student[] }>(routes.students);

  return (
    <div className="flex gap-2 md:w-1/2">
      <MultiSelect
        disabled={courses.isLoading}
        value={selectedCourses}
        onChange={onCoursesChange}
        buttonContent={
          courses.isLoading ? (
            <>Loading...</>
          ) : selectedCourses.length === 0 ? (
            <>All courses</>
          ) : selectedCourses.length === 1 ? (
            selectedCourses[0].title
          ) : (
            <>{selectedCourses.length} courses</>
          )
        }
      >
        {courses.data?.courses.map(course => (
          <MultiSelect.Option key={`course_${course.id}`} value={course}>
            {course.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={assignments.isLoading}
        value={selectedAssignments}
        onChange={onAssignmentsChange}
        buttonContent={
          assignments.isLoading ? (
            <>Loading...</>
          ) : selectedAssignments.length === 0 ? (
            <>All assignments</>
          ) : selectedAssignments.length === 1 ? (
            selectedAssignments[0].title
          ) : (
            <>{selectedAssignments.length} assignments</>
          )
        }
      >
        {assignments.data?.assignments.map(assignment => (
          <MultiSelect.Option
            key={`assignment_${assignment.id}`}
            value={assignment}
          >
            {assignment.title}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
      <MultiSelect
        disabled={students.isLoading}
        value={selectedStudents}
        onChange={onStudentsChange}
        buttonContent={
          students.isLoading ? (
            <>Loading...</>
          ) : selectedStudents.length === 0 ? (
            <>All students</>
          ) : selectedStudents.length === 1 ? (
            selectedStudents[0].display_name
          ) : (
            <>{selectedStudents.length} students</>
          )
        }
      >
        {students.data?.students.map(student => (
          <MultiSelect.Option key={student.lms_id} value={student}>
            {student.display_name}
          </MultiSelect.Option>
        ))}
      </MultiSelect>
    </div>
  );
}
