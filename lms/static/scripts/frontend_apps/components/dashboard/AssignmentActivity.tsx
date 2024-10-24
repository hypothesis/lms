import { ClockIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useMemo, useState } from 'preact/hooks';
import { useLocation, useParams, useSearch } from 'wouter-preact';

import type {
  AssignmentDetails,
  GradingSync,
  StudentGradingSync,
  StudentGradingSyncStatus,
  StudentsMetricsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch, usePolledAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { courseURL } from '../../utils/dashboard/navigation';
import { rootViewTitle } from '../../utils/dashboard/root-view-title';
import { useDocumentTitle } from '../../utils/hooks';
import { type QueryParams, replaceURLParams } from '../../utils/url';
import RelativeTime from '../RelativeTime';
import type {
  DashboardActivityFiltersProps,
  SegmentsType,
} from './DashboardActivityFilters';
import DashboardActivityFilters from './DashboardActivityFilters';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import FormattedDate from './FormattedDate';
import GradeIndicator from './GradeIndicator';
import type { OrderableActivityTableColumn } from './OrderableActivityTable';
import OrderableActivityTable from './OrderableActivityTable';
import SyncGradesButton from './SyncGradesButton';

type StudentsTableRow = {
  lms_id: string;
  h_userid: string;
  display_name: string | null;
  last_activity: string | null;
  annotations: number;
  replies: number;

  /** Currently calculated grade, only for auto-grading assignments */
  current_grade?: number;

  /**
   * Grade that was submitted to the LMS in the most recent sync.
   * If no grade has ever been synced, this will be `null`.
   * If the assignment is not auto-grading, this will be ´undefined`.
   */
  last_grade?: number | null;
};

/**
 * Error to display when last grades sync failed, showing the number of
 * individual student syncs that failed
 */
function SyncErrorMessage({ grades }: { grades: StudentGradingSync[] }) {
  const count = useMemo(
    () => grades.filter(g => g.status === 'failed').length,
    [grades],
  );

  return (
    <div
      className={classnames(
        'rounded px-2 py-1',
        'font-bold text-grade-error bg-grade-error-light',
      )}
    >
      Error syncing {count} {count === 1 ? 'grade' : 'grades'}
    </div>
  );
}

/**
 * Activity in a list of students that are part of a specific assignment
 */
export default function AssignmentActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const {
    routes,
    auto_grading_sync_enabled,
    assignment_segments_filter_enabled,
  } = dashboard;
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
  const isAutoGradingAssignment = !!assignment.data?.auto_grading_config;
  const segments = useMemo((): DashboardActivityFiltersProps['segments'] => {
    const { data } = assignment;
    if (
      !data ||
      // Display the segments filter only for auto-grading assignments, or
      // assignments where the feature was explicitly enabled
      (!assignment_segments_filter_enabled && !isAutoGradingAssignment)
    ) {
      return undefined;
    }

    const hasSections = 'sections' in data;
    const hasGroups = 'groups' in data;
    const entries = hasSections
      ? data.sections
      : hasGroups
        ? data.groups
        : undefined;
    const type: SegmentsType = hasSections
      ? 'sections'
      : hasGroups
        ? 'groups'
        : 'none';

    return {
      type,
      entries: entries ?? [],
      selectedIds: segmentIds,
      onChange: segmentIds => updateFilters({ segmentIds }),
    };
  }, [
    assignment,
    assignment_segments_filter_enabled,
    isAutoGradingAssignment,
    segmentIds,
    updateFilters,
  ]);

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
    if (!isAutoGradingAssignment || !students.data) {
      return undefined;
    }

    return students.data.students
      .filter(
        ({ auto_grading_grade }) =>
          !!auto_grading_grade &&
          auto_grading_grade.current_grade !== auto_grading_grade.last_grade,
      )
      .map(({ h_userid, auto_grading_grade }) => ({
        h_userid,
        grade: auto_grading_grade?.current_grade ?? 0,
      }));
  }, [isAutoGradingAssignment, students.data]);

  const syncURL = useMemo(
    () =>
      isAutoGradingAssignment
        ? replaceURLParams(routes.assignment_grades_sync, {
            assignment_id: assignmentId,
          })
        : null,
    [assignmentId, isAutoGradingAssignment, routes.assignment_grades_sync],
  );
  const [lastSyncParams, setLastSyncParams] = useState<QueryParams>({});
  const lastSync = usePolledAPIFetch<GradingSync>({
    path: syncURL,
    params: lastSyncParams,
    // Keep polling as long as sync is in progress
    shouldRefresh: result =>
      !!result.data &&
      ['scheduled', 'in_progress'].includes(result.data.status),
  });
  const studentSyncStatuses = useMemo(() => {
    const studentStatusMap: Record<string, StudentGradingSyncStatus> = {};
    for (const { h_userid, status } of lastSync.data?.grades ?? []) {
      studentStatusMap[h_userid] = status;
    }

    return studentStatusMap;
  }, [lastSync.data?.grades]);

  const onSyncScheduled = useCallback(() => {
    // Once the request succeeds, we update the params so that polling the
    // status is triggered again
    setLastSyncParams({ t: `${Date.now()}` });

    students.mutate({
      students: (students.data?.students ?? []).map(
        ({ auto_grading_grade, ...rest }) =>
          !auto_grading_grade
            ? rest
            : {
                ...rest,
                auto_grading_grade: {
                  ...auto_grading_grade,
                  // Once a sync has been scheduled, update last_grade with
                  // current_grade value, so that students are no longer
                  // labelled as "New"
                  last_grade: auto_grading_grade.current_grade,
                },
              },
      ),
    });
  }, [students]);

  const rows: StudentsTableRow[] = useMemo(
    () =>
      (students.data?.students ?? []).map(
        ({ annotation_metrics, auto_grading_grade, ...rest }) => ({
          ...auto_grading_grade,
          ...annotation_metrics,
          ...rest,
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

    if (isAutoGradingAssignment) {
      firstColumns.push({
        field: 'current_grade',
        label: 'Grade',
      });
    }

    return [...firstColumns, ...lastColumns];
  }, [isAutoGradingAssignment]);

  const title = assignment.data?.title ?? 'Untitled assignment';
  useDocumentTitle(title);

  return (
    <div className="flex flex-col gap-y-5">
      <div>
        {assignment.data && (
          <div className="mb-3 mt-1 w-full flex items-center">
            <DashboardBreadcrumbs
              links={[
                {
                  title: rootViewTitle(dashboard),
                  href: urlWithFilters({ studentIds }, { path: '' }),
                },
                {
                  title: assignment.data.course.title,
                  href: urlWithFilters(
                    { studentIds },
                    { path: courseURL(assignment.data.course.id) },
                  ),
                },
              ]}
            />
            {lastSync.data && (
              <div
                className="flex gap-x-1 items-center text-color-text-light"
                data-testid="last-sync-date"
              >
                <ClockIcon />
                Grades last synced:{' '}
                {lastSync.data.finish_date ? (
                  <RelativeTime dateTime={lastSync.data.finish_date} />
                ) : (
                  'syncing…'
                )}
              </div>
            )}
          </div>
        )}
        <div className="flex justify-between items-center">
          <h2 className="text-lg text-brand font-semibold" data-testid="title">
            {assignment.isLoading && 'Loading...'}
            {assignment.error && 'Could not load assignment title'}
            {assignment.data && title}
          </h2>
          <div aria-live="polite" aria-relevant="additions">
            {lastSync.data && lastSync.data.status === 'failed' && (
              <SyncErrorMessage grades={lastSync.data.grades} />
            )}
          </div>
        </div>
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
        {isAutoGradingAssignment && auto_grading_sync_enabled && (
          <SyncGradesButton
            studentsToSync={studentsToSync}
            lastSync={lastSync}
            onSyncScheduled={onSyncScheduled}
          />
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
            case 'current_grade':
              return (
                <div
                  className={classnames(
                    // Add a bit of vertical negative margin to avoid the chip
                    // component to make rows too tall
                    '-my-0.5',
                  )}
                >
                  <GradeIndicator
                    grade={stats.current_grade ?? 0}
                    lastGrade={stats.last_grade}
                    annotations={stats.annotations}
                    replies={stats.replies}
                    status={studentSyncStatuses[stats.h_userid]}
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
