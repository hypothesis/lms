import {
  CautionIcon,
  ClockIcon,
  FileGenericIcon,
  InfoIcon,
  Link,
} from '@hypothesis/frontend-shared';
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
import type {
  DashboardActivityFiltersProps,
  SegmentsType,
} from './DashboardActivityFilters';
import DashboardActivityFilters from './DashboardActivityFilters';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import FormattedDate from './FormattedDate';
import GradeIndicator from './GradeIndicator';
import LastSyncIndicator from './LastSyncIndicator';
import type { OrderableActivityTableColumn } from './OrderableActivityTable';
import OrderableActivityTable from './OrderableActivityTable';
import StudentStatusBadge from './StudentStatusBadge';
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

  /** Whether this student is active in the course/assignment or roster */
  active: boolean;

  // Only present for checkpoint-enabled assignments. Quick/functional
  // columns: flattened from `checkpoint_metrics`, not grouped visually yet.
  checkpoint_annotations?: number;
  checkpoint_replies?: number;
  checkpoint_grade?: number;
  due_date_annotations?: number;
  due_date_replies?: number;
  due_date_grade?: number;
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
        'font-bold text-red-dark bg-red-light',
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
  const { routes, user } = dashboard;
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
  const isGradable = !!assignment.data?.is_gradable;
  const segments = useMemo((): DashboardActivityFiltersProps['segments'] => {
    const { data } = assignment;
    if (!data) {
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
  }, [assignment, segmentIds, updateFilters]);

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
        ({ auto_grading_grade, active }) =>
          active &&
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
      isAutoGradingAssignment && isGradable
        ? replaceURLParams(routes.assignment_grades_sync, {
            assignment_id: assignmentId,
          })
        : null,
    [
      assignmentId,
      isAutoGradingAssignment,
      isGradable,
      routes.assignment_grades_sync,
    ],
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
      last_updated: students.data?.last_updated ?? null,
    });
  }, [students]);

  const rows: StudentsTableRow[] = useMemo(
    () =>
      (students.data?.students ?? []).map(
        ({
          annotation_metrics,
          auto_grading_grade,
          checkpoint_metrics,
          ...rest
        }) => ({
          ...auto_grading_grade,
          ...annotation_metrics,
          ...rest,
          ...(checkpoint_metrics && {
            checkpoint_annotations: checkpoint_metrics.checkpoint.annotations,
            checkpoint_replies: checkpoint_metrics.checkpoint.replies,
            checkpoint_grade: checkpoint_metrics.checkpoint_grade,
            due_date_annotations: checkpoint_metrics.due_date.annotations,
            due_date_replies: checkpoint_metrics.due_date.replies,
            due_date_grade: checkpoint_metrics.due_date_grade,
          }),
        }),
      ),
    [students.data],
  );
  const isCheckpointAssignment = !!assignment.data?.checkpoint_enabled;
  const columns = useMemo(() => {
    const width = isCheckpointAssignment
      ? {
          display_name: 'w-[200px]',
          grade: 'w-[90px]',
          count: 'w-[110px]',
          last_activity: 'w-[130px]',
        }
      : {};

    const firstColumns: OrderableActivityTableColumn<StudentsTableRow>[] = [
      {
        field: 'display_name',
        label: 'Student',
        ...(width.display_name && { width: width.display_name }),
      },
    ];
    const lastColumns: OrderableActivityTableColumn<StudentsTableRow>[] = [
      {
        field: 'annotations',
        label: 'Annotations',
        initialOrderDirection: 'descending',
        ...(width.count && { width: width.count }),
      },
      {
        field: 'replies',
        label: 'Replies',
        initialOrderDirection: 'descending',
        ...(width.count && { width: width.count }),
      },
      {
        field: 'last_activity',
        label: 'Last Activity',
        initialOrderDirection: 'descending',
        ...(width.last_activity && { width: width.last_activity }),
      },
    ];

    if (isAutoGradingAssignment) {
      firstColumns.push({
        field: 'current_grade',
        label: 'Grade',
        ...(width.grade && { width: width.grade }),
      });
    }

    // TODO: these render as plain flat columns for now (functional, not
    // grouped visually into "Checkpoint" / "Due Date" headers like the
    // mockup). `OrderableActivityTable` only supports a single header row
    // today, so grouping needs a follow-up there.
    const checkpointColumns: OrderableActivityTableColumn<StudentsTableRow>[] =
      isCheckpointAssignment
        ? [
            {
              field: 'checkpoint_annotations',
              label: 'Checkpoint Annot.',
              initialOrderDirection: 'descending',
              width: width.count,
            },
            {
              field: 'checkpoint_replies',
              label: 'Checkpoint Replies',
              initialOrderDirection: 'descending',
              width: width.count,
            },
            {
              field: 'due_date_annotations',
              label: 'Due Date Annot.',
              initialOrderDirection: 'descending',
              width: width.count,
            },
            {
              field: 'due_date_replies',
              label: 'Due Date Replies',
              initialOrderDirection: 'descending',
              width: width.count,
            },
          ]
        : [];
    if (isCheckpointAssignment && isAutoGradingAssignment) {
      checkpointColumns.push(
        {
          field: 'checkpoint_grade',
          label: 'Checkpoint Grade',
          width: width.grade,
        },
        {
          field: 'due_date_grade',
          label: 'Due Date Grade',
          width: width.grade,
        },
      );
    }

    return [...firstColumns, ...checkpointColumns, ...lastColumns];
  }, [isAutoGradingAssignment, isCheckpointAssignment]);
  const minTableWidth = isCheckpointAssignment
    ? columns.length * 110 + 100
    : undefined;

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
            <div className="flex gap-0.5">
              {lastSync.data && (
                <LastSyncIndicator
                  icon={
                    lastSync.data.status === 'failed' ? CautionIcon : ClockIcon
                  }
                  taskName="Grades"
                  dateTime={lastSync.data.finish_date}
                  data-testid="last-sync-date"
                />
              )}
              {students.data?.last_updated && (
                <LastSyncIndicator
                  icon={FileGenericIcon}
                  taskName="Roster"
                  dateTime={students.data.last_updated}
                  data-testid="last-roster-date"
                />
              )}
            </div>
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
        {isAutoGradingAssignment && !user.is_staff && isGradable && (
          <SyncGradesButton
            studentsToSync={studentsToSync}
            lastSync={lastSync}
            onSyncScheduled={onSyncScheduled}
          />
        )}
      </div>
      <div
        className={classnames({ 'overflow-x-auto': isCheckpointAssignment })}
      >
        <div style={minTableWidth ? { minWidth: minTableWidth } : undefined}>
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
                case 'checkpoint_annotations':
                case 'checkpoint_replies':
                case 'due_date_annotations':
                case 'due_date_replies':
                  return <div className="text-right">{stats[field] ?? 0}</div>;
                case 'checkpoint_grade':
                case 'due_date_grade':
                  return (
                    <div className="text-right">
                      {stats[field] !== undefined
                        ? `${Math.round(stats[field] * 100)}%`
                        : ''}
                    </div>
                  );
                case 'last_activity':
                  return stats.last_activity ? (
                    <FormattedDate date={stats.last_activity} />
                  ) : (
                    ''
                  );
                case 'display_name':
                  return (
                    <div className="flex items-center justify-between gap-x-2">
                      {stats.display_name ?? (
                        <span className="flex flex-col gap-1.5">
                          <span className="italic">Unknown</span>
                          <span className="text-xs text-grey-7">
                            This student launched the assignment but didn{"'"}t
                            annotate yet
                          </span>
                        </span>
                      )}
                      {!stats.active && (
                        <div
                          className="-my-0.5"
                          title="This student is no longer in this assignment"
                        >
                          <StudentStatusBadge type="drop" />
                        </div>
                      )}
                    </div>
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
      </div>
      {!students.isLoading && !students.data?.last_updated && (
        <Link
          variant="text-light"
          classes="flex items-center gap-1"
          href="https://web.hypothes.is/help/student-roster-displays-in-the-lms-reporting-dashboards/"
          target="_blank"
          data-testid="missing-roster-message"
        >
          <InfoIcon />
          Full roster data for this assignment is not available. This only shows
          students who have previously launched it.
        </Link>
      )}
    </div>
  );
}
