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
import LastSyncIndicator from './LastSyncIndicator';
import OrderableActivityTable from './OrderableActivityTable';
import SyncGradesButton from './SyncGradesButton';
import {
  assignmentSyncsGrades,
  useStudentsTableConfig,
  useStudentsToSync,
} from './students-table';

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
  // Whether this assignment's variant grades students. `isGradable` and
  // `is_staff` are not variant-specific: they gate the sync for every variant.
  const syncsGrades = assignmentSyncsGrades(assignment.data);
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
  const studentsToSync = useStudentsToSync({
    students: students.data?.students,
    assignment: assignment.data,
  });

  const syncURL = useMemo(
    () =>
      syncsGrades && isGradable
        ? replaceURLParams(routes.assignment_grades_sync, {
            assignment_id: assignmentId,
          })
        : null,
    [assignmentId, syncsGrades, isGradable, routes.assignment_grades_sync],
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

    // TODO: This is the last bit of this view which knows what kind of
    // assignment it is displaying: `auto_grading_grade` only exists in the
    // auto-grading variant, so a variant storing its grades anywhere else (per
    // checkpoint, say) would keep labelling them as "New". Move it into the
    // variant module as `markGradesAsSynced`, next to `gradesToSync`, when that
    // second variant lands: designing the method against two real callers beats
    // guessing its shape from this one.
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

  const { rows, columns, renderItem } = useStudentsTableConfig({
    students: students.data?.students,
    assignment: assignment.data,
    studentSyncStatuses,
  });

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
        {syncsGrades && !user.is_staff && isGradable && (
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
        renderItem={renderItem}
      />
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
