import { Link } from '@hypothesis/frontend-shared';
import { useMemo, useState } from 'preact/hooks';
import { Link as RouterLink, useParams } from 'wouter-preact';

import type {
  Assignment,
  Course,
  CoursesResponse,
  Student,
} from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { useDocumentTitle } from '../../utils/hooks';
import { replaceURLParams } from '../../utils/url';
import DashboardActivityFilters from './DashboardActivityFilters';
import FormattedDate from './FormattedDate';
import OrderableActivityTable from './OrderableActivityTable';

type CoursesTableRow = {
  id: number;
  title: string;
  assignments: number;
  last_launched: string | null;
};

const courseURL = (id: number) => urlPath`/courses/${String(id)}`;

/**
 * List of courses that belong to a specific organization
 */
export default function OrganizationActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const { organizationPublicId } = useParams<{
    organizationPublicId: string;
  }>();

  useDocumentTitle('All courses');

  const [selectedStudents, setSelectedStudents] = useState<Student[]>([]);
  const [selectedAssignments, setSelectedAssignments] = useState<Assignment[]>(
    [],
  );
  const [selectedCourses, setSelectedCourses] = useState<Course[]>([]);
  const studentIds = useMemo(
    () => selectedStudents.map(s => s.h_userid),
    [selectedStudents],
  );
  const assignmentIds = useMemo(
    () => selectedAssignments.map(a => `${a.id}`),
    [selectedAssignments],
  );
  const courseIds = useMemo(
    () => selectedCourses.map(c => `${c.id}`),
    [selectedCourses],
  );

  const courses = useAPIFetch<CoursesResponse>(
    replaceURLParams(routes.organization_courses, {
      organization_public_id: organizationPublicId,
    }),
    {
      h_userid: studentIds,
      assignment_id: assignmentIds,
      course_id: courseIds,
    },
  );
  const rows: CoursesTableRow[] = useMemo(
    () =>
      courses.data?.courses.map(({ id, title, course_metrics }) => ({
        id,
        title,
        ...course_metrics,
      })) ?? [],
    [courses.data],
  );

  return (
    <div className="flex flex-col gap-y-5">
      <h2 className="text-lg text-brand font-semibold">All courses</h2>
      <DashboardActivityFilters
        selectedStudents={selectedStudents}
        onStudentsChange={setSelectedStudents}
        selectedAssignments={selectedAssignments}
        onAssignmentsChange={setSelectedAssignments}
        selectedCourses={selectedCourses}
        onCoursesChange={setSelectedCourses}
      />
      <OrderableActivityTable
        loading={courses.isLoading}
        title="Courses"
        emptyMessage={
          courses.error ? 'Could not load courses' : 'No courses found'
        }
        rows={rows}
        columns={[
          {
            field: 'title',
            label: 'Course title',
          },
          {
            field: 'assignments',
            label: 'Assignments',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_launched',
            label: 'Last launched',
            initialOrderDirection: 'descending',
          },
        ]}
        defaultOrderField="title"
        renderItem={(stats, field) => {
          if (field === 'assignments') {
            return <div className="text-right">{stats[field]}</div>;
          } else if (field === 'last_launched') {
            return stats.last_launched ? (
              <FormattedDate date={stats.last_launched} />
            ) : (
              ''
            );
          }

          return (
            <RouterLink href={urlPath`/courses/${String(stats.id)}`} asChild>
              <Link underline="always" variant="text">
                {stats.title}
              </Link>
            </RouterLink>
          );
        }}
        navigateOnConfirmRow={stats => courseURL(stats.id)}
      />
    </div>
  );
}
