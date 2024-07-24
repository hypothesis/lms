import { Link } from '@hypothesis/frontend-shared';
import { useMemo, useState } from 'preact/hooks';
import { Link as RouterLink, useParams, useLocation } from 'wouter-preact';

import type {
  Assignment,
  AssignmentsResponse,
  Course,
  Student,
} from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { assignmentURL, courseURL } from '../../utils/dashboard/navigation';
import { recordToQueryStringFragment, replaceURLParams } from '../../utils/url';
import DashboardActivityFilters from './DashboardActivityFilters';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import FormattedDate from './FormattedDate';
import OrderableActivityTable from './OrderableActivityTable';

type AssignmentsTableRow = {
  id: number;
  title: string;
  last_activity: string | null;
  annotations: number;
  replies: number;
};

/**
 * Activity in a list of assignments that are part of a specific course
 */
export default function CourseActivity() {
  const [, navigate] = useLocation();
  const { courseId } = useParams<{ courseId: string }>();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const [selectedStudents, setSelectedStudents] = useState<Student[]>([]);
  const [selectedAssignments, setSelectedAssignments] = useState<Assignment[]>(
    [],
  );
  const filteringQuery = useMemo(
    () => ({
      h_userid: selectedStudents.map(s => s.h_userid),
      assignment_id: selectedAssignments.map(a => `${a.id}`),
    }),
    [selectedAssignments, selectedStudents],
  );

  const course = useAPIFetch<Course>(
    replaceURLParams(routes.course, { course_id: courseId }),
  );
  const assignments = useAPIFetch<AssignmentsResponse>(
    replaceURLParams(routes.course_assignments_metrics, {
      course_id: courseId,
    }),
    filteringQuery,
  );

  const rows: AssignmentsTableRow[] = useMemo(
    () =>
      (assignments.data?.assignments ?? []).map(
        ({ id, title, annotation_metrics }) => ({
          id,
          title,
          ...annotation_metrics,
        }),
      ),
    [assignments.data],
  );

  return (
    <div className="flex flex-col gap-y-5">
      <div>
        <div className="mb-3 mt-1 w-full">
          <DashboardBreadcrumbs />
        </div>
        <h2 className="text-lg text-brand font-semibold" data-testid="title">
          {course.isLoading && 'Loading...'}
          {course.error && 'Could not load course title'}
          {course.data && course.data.title}
        </h2>
      </div>
      <DashboardActivityFilters
        selectedCourses={course.data ? [course.data] : []}
        onCoursesChange={courses => {
          const firstDifferentCourse = courses.find(
            c => `${c.id}` !== courseId,
          );
          if (firstDifferentCourse) {
            // When a course other than the "active" one (the one represented
            // in the URL) is selected, navigate to that course and propagate
            // the rest of the filters.
            const queryString = recordToQueryStringFragment(filteringQuery);
            navigate(`${courseURL(firstDifferentCourse.id)}${queryString}`);
          }
        }}
        selectedAssignments={selectedAssignments}
        onAssignmentsChange={setSelectedAssignments}
        selectedStudents={selectedStudents}
        onStudentsChange={setSelectedStudents}
      />
      <OrderableActivityTable
        loading={assignments.isLoading}
        title={course.data?.title ?? 'Loading...'}
        emptyMessage={
          assignments.error
            ? 'Could not load assignments'
            : 'No assignments found'
        }
        rows={rows}
        columns={[
          {
            field: 'title',
            label: 'Assignment',
          },
          {
            field: 'annotations',
            label: 'Annotations',
            initialOrderDirection: 'descending',
          },
          {
            field: 'replies',
            label: 'Replies',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_activity',
            label: 'Last Activity',
            initialOrderDirection: 'descending',
          },
        ]}
        defaultOrderField="title"
        renderItem={(stats, field) => {
          if (['annotations', 'replies'].includes(field)) {
            return <div className="text-right">{stats[field]}</div>;
          } else if (field === 'title') {
            return (
              <RouterLink href={assignmentURL(stats.id)} asChild>
                <Link underline="always" variant="text">
                  {stats.title}
                </Link>
              </RouterLink>
            );
          }

          return (
            stats.last_activity && <FormattedDate date={stats.last_activity} />
          );
        }}
        navigateOnConfirmRow={stats => assignmentURL(stats.id)}
      />
    </div>
  );
}
