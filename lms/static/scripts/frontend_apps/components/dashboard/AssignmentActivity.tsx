import classnames from 'classnames';
import { useMemo } from 'preact/hooks';
import { useLocation, useParams, useSearch } from 'wouter-preact';

import type {
  AssignmentDetails,
  StudentsMetricsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { courseURL } from '../../utils/dashboard/navigation';
import { useDocumentTitle } from '../../utils/hooks';
import { replaceURLParams } from '../../utils/url';
import type { DashboardActivityFiltersProps } from './DashboardActivityFilters';
import DashboardActivityFilters from './DashboardActivityFilters';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import FormattedDate from './FormattedDate';
import GradeIndicator from './GradeIndicator';
import type { OrderableActivityTableColumn } from './OrderableActivityTable';
import OrderableActivityTable from './OrderableActivityTable';
import SyncGradesButton from './SyncGradesButton';

type StudentsTableRow = {
  lms_id: string;
  display_name: string | null;
  last_activity: string | null;
  annotations: number;
  replies: number;
  auto_grading_grade?: number;
};

/**
 * Activity in a list of students that are part of a specific assignment
 */
export default function AssignmentActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { routes, auto_grading_sync_enabled } = dashboard;
  const { assignmentId, organizationPublicId } = useParams<{
    assignmentId: string;
    organizationPublicId?: string;
  }>();

  const { filters, updateFilters, urlWithFilters } = useDashboardFilters();
  const { studentIds, segmentIds } = filters;
  const search = useSearch();
  const [, navigate] = useLocation();

  const assignment = useAPIFetch<AssignmentDetails>(
    replaceURLParams(routes.assignment, { assignment_id: assignmentId }),
  );
  const autoGradingEnabled = !!assignment.data?.auto_grading_config;
  const segments = useMemo((): DashboardActivityFiltersProps['segments'] => {
    const { data } = assignment;
    // For now, we want to display the segments filter only for auto-grading
    // assignments, but this will eventually change
    if (!data || !autoGradingEnabled) {
      return undefined;
    }

    const hasSections = 'sections' in data;
    const entries = hasSections
      ? data.sections
      : 'groups' in data
        ? data.groups
        : undefined;

    // If the assignment doesn't have either sections or groups, we won't
    // display the segments filter
    if (!entries || entries.length === 0) {
      return undefined;
    }

    return {
      type: hasSections ? 'sections' : 'groups',
      entries,
      selectedIds: segmentIds,
      onChange: segmentIds => updateFilters({ segmentIds }),
    };
  }, [assignment, autoGradingEnabled, segmentIds, updateFilters]);

  const students = useAPIFetch<StudentsMetricsResponse>(
    routes.students_metrics,
    {
      h_userid: studentIds,
      segment_authority_provided_id: segmentIds,
      assignment_id: assignmentId,
      org_public_id: organizationPublicId,
    },
  );

  const studentsToSync = useMemo(() => {
    if (!autoGradingEnabled) {
      return [];
    }

    // TODO Filter out students whose grades didn't change
    return (students.data?.students ?? []).map(
      ({ h_userid, auto_grading_grade = 0 }) => ({
        h_userid,
        grade: auto_grading_grade,
      }),
    );
  }, [autoGradingEnabled, students.data?.students]);
  const rows: StudentsTableRow[] = useMemo(
    () =>
      (students.data?.students ?? []).map(
        ({ annotation_metrics, ...rest }) => ({
          ...rest,
          ...annotation_metrics,
        }),
      ),
    [students.data],
  );
  const columns = useMemo(() => {
    const firstColumns: OrderableActivityTableColumn<StudentsTableRow>[] = [
      {
        field: 'display_name',
        label: 'Student',
      },
    ];
    const lastColumns: OrderableActivityTableColumn<StudentsTableRow>[] = [
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
    ];

    if (autoGradingEnabled) {
      firstColumns.push({
        field: 'auto_grading_grade',
        label: 'Grade',
      });
    }

    return [...firstColumns, ...lastColumns];
  }, [autoGradingEnabled]);

  const title = assignment.data?.title ?? 'Untitled assignment';
  useDocumentTitle(title);

  return (
    <div className="flex flex-col gap-y-5">
      <div>
        {assignment.data && (
          <div className="mb-3 mt-1 w-full">
            <DashboardBreadcrumbs
              allCoursesLink={urlWithFilters({ studentIds }, { path: '' })}
              links={[
                {
                  title: assignment.data.course.title,
                  href: urlWithFilters(
                    { studentIds },
                    { path: courseURL(assignment.data.course.id) },
                  ),
                },
              ]}
            />
          </div>
        )}
        <h2 className="text-lg text-brand font-semibold" data-testid="title">
          {assignment.isLoading && 'Loading...'}
          {assignment.error && 'Could not load assignment title'}
          {assignment.data && title}
        </h2>
      </div>
      <div className="flex justify-between items-end gap-x-4">
        {assignment.data && (
          <DashboardActivityFilters
            courses={{
              activeItem: assignment.data.course,
              // When the active course is cleared, navigate to home, but keep
              // active assignment and students
              onClear: () =>
                navigate(
                  urlWithFilters(
                    { studentIds, assignmentIds: [assignmentId] },
                    { path: '' },
                  ),
                ),
            }}
            assignments={{
              activeItem: assignment.data,
              // When active assignment is cleared, navigate to its course page,
              // but keep other query params intact
              onClear: () => {
                const query = search.length === 0 ? '' : `?${search}`;
                navigate(`${courseURL(assignment.data!.course.id)}${query}`);
              },
            }}
            students={{
              selectedIds: studentIds,
              onChange: studentIds => updateFilters({ studentIds }),
            }}
            segments={segments}
            onClearSelection={
              studentIds.length > 0 ||
              (segments && segments.selectedIds.length > 0)
                ? () => updateFilters({ studentIds: [], segmentIds: [] })
                : undefined
            }
          />
        )}
        {autoGradingEnabled && auto_grading_sync_enabled && (
          <SyncGradesButton studentsToSync={studentsToSync} />
        )}
      </div>
      <OrderableActivityTable
        loading={students.isLoading}
        title={assignment.isLoading ? 'Loading...' : title}
        emptyMessage={
          students.error ? 'Could not load students' : 'No students found'
        }
        rows={rows}
        columns={columns}
        defaultOrderField="display_name"
        renderItem={(stats, field) => {
          switch (field) {
            case 'annotations':
            case 'replies':
              return <div className="text-right">{stats[field]}</div>;
            case 'last_activity':
              return stats.last_activity ? (
                <FormattedDate date={stats.last_activity} />
              ) : (
                ''
              );
            case 'display_name':
              return (
                stats.display_name ?? (
                  <span className="flex flex-col gap-1.5">
                    <span className="italic">Unknown</span>
                    <span className="text-xs text-grey-7">
                      This student launched the assignment but didn{"'"}t
                      annotate yet
                    </span>
                  </span>
                )
              );
            case 'auto_grading_grade':
              return (
                <div
                  className={classnames(
                    // Add a bit of vertical negative margin to avoid the chip
                    // component to make rows too tall
                    '-my-0.5',
                  )}
                >
                  <GradeIndicator
                    grade={stats.auto_grading_grade ?? 0}
                    annotations={stats.annotations}
                    replies={stats.replies}
                    config={assignment.data?.auto_grading_config}
                  />
                </div>
              );
            default:
              return '';
          }
        }}
      />
    </div>
  );
}
