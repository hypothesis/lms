import {
  FilterClearIcon,
  LinkButton,
  MultiSelect,
  formatDateTime,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { MutableRef } from 'preact/hooks';
import { useMemo } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type {
  Assignment,
  AssignmentSegment,
  AssignmentsResponse,
  Course,
  CoursesResponse,
  Student,
  StudentsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { usePaginatedAPIFetch } from '../../utils/api';
import TruncatedText from '../TruncatedText';
import ContentWithBadge from './ContentWithBadge';
import PaginatedMultiSelect from './PaginatedMultiSelect';

/**
 * Allow the user to select items from a paginated list of all items matching
 * the current filters.
 * The set of currently selected items are maintained by the parent component.
 */
export type ActivityFilterSelection = {
  /**
   * Currently, only the first item here is taken into consideration.
   * This will change as soon as we support multi-selection, without having to
   * change the component's props API.
   */
  selectedIds: string[];

  /**
   * Invoked when selected items change.
   * It will be called with an array of 1 or 0 items, indicating either one item
   * or no items are selected.
   */
  onChange: (newSelectedIds: string[]) => void;
};

/**
 * Display two items in the dropdown, one for an active / selected item and one
 * to clear the selection.
 */
export type ActivityFilterItem<T extends Course | Assignment> = {
  activeItem: T;
  onClear: () => void;
};

export type SegmentsType = 'groups' | 'sections' | 'none';

export type SegmentsSelection = ActivityFilterSelection & {
  type: SegmentsType;
  entries: AssignmentSegment[];
};

export type DashboardActivityFiltersProps = {
  courses: ActivityFilterSelection | ActivityFilterItem<Course>;
  assignments: ActivityFilterSelection | ActivityFilterItem<Assignment>;

  /**
   * Configuration for the segments filter.
   * It is relevant only when listing students, so not providing this will
   * prevent that filter to be rendered or taken into consideration in any
   * way.
   * Unlike other filters, the entries are not loaded by this component but
   * provided as part of the props.
   */
  segments?: SegmentsSelection;

  students: ActivityFilterSelection;
  onClearSelection?: () => void;
};

type PropsWithElementRef<T> = T & {
  /** Ref to be used on a `Select.Option` element */
  elementRef?: MutableRef<HTMLElement | null>;
};

/**
 * Represents a `Select.Option` for a specific assignment
 */
function AssignmentOption({
  assignment,
  elementRef,
}: PropsWithElementRef<{ assignment: Assignment }>) {
  return (
    <MultiSelect.Option value={`${assignment.id}`} elementRef={elementRef}>
      <div className="flex flex-col gap-0.5">
        <TruncatedText>{assignment.title}</TruncatedText>
        <div className="text-grey-6 text-xs">
          {formatDateTime(assignment.created)}
        </div>
      </div>
    </MultiSelect.Option>
  );
}

/**
 * Represents a `Select.Option` for a specific student
 */
function StudentOption({
  student,
  elementRef,
}: PropsWithElementRef<{ student: Student }>) {
  const hasDisplayName = !!student.display_name;
  const displayName =
    student.display_name ??
    `Student name unavailable (ID: ${student.lms_id.substring(0, 5)})`;

  return (
    <MultiSelect.Option value={student.h_userid} elementRef={elementRef}>
      <TruncatedText
        classes={hasDisplayName ? undefined : 'italic'}
        title={hasDisplayName ? undefined : `User ID: ${student.lms_id}`}
        data-testid="option-content-wrapper"
      >
        {displayName}
      </TruncatedText>
    </MultiSelect.Option>
  );
}

/**
 * A MultiSelect to list a collection of groups or sections (AKA segments).
 */
function SegmentsMultiSelect({ segments }: { segments: SegmentsSelection }) {
  const segmentsName = segments.type === 'groups' ? 'groups' : 'sections';
  const segmentNameSingular = segments.type === 'groups' ? 'group' : 'section';
  const isNoneType = segments.type === 'none';

  return (
    <MultiSelect
      aria-label={`Select ${segmentsName}`}
      containerClasses={classnames('!w-auto', { 'min-w-44': !isNoneType })}
      value={segments.selectedIds}
      onChange={newSegmentIds => segments.onChange(newSegmentIds)}
      disabled={segments.entries.length === 0}
      buttonContent={
        isNoneType ? (
          'No sections/groups'
        ) : segments.selectedIds.length === 0 ? (
          <ContentWithBadge count={segments.entries.length}>
            All {segmentsName}
          </ContentWithBadge>
        ) : segments.selectedIds.length === 1 ? (
          (segments.entries.find(
            s => s.h_authority_provided_id === segments.selectedIds[0],
          )?.name ?? `1 ${segmentNameSingular}`)
        ) : (
          <>
            {segments.selectedIds.length} {segmentsName}
          </>
        )
      }
      data-testid="segments-select"
    >
      <MultiSelect.Option value={undefined}>
        All {segmentsName}
      </MultiSelect.Option>
      {segments.entries.map(entry => (
        <MultiSelect.Option
          key={entry.h_authority_provided_id}
          value={entry.h_authority_provided_id}
        >
          <TruncatedText>{entry.name}</TruncatedText>
        </MultiSelect.Option>
      ))}
    </MultiSelect>
  );
}

/**
 * Renders drop-downs to select courses, assignments and/or students, used to
 * filter dashboard activity metrics.
 */
export default function DashboardActivityFilters({
  courses,
  assignments,
  segments,
  students,
  onClearSelection,
}: DashboardActivityFiltersProps) {
  const { dashboard } = useConfig(['dashboard']);
  const { organizationPublicId } = useParams();
  const { routes } = dashboard;

  const [selectedCourseIds, activeCourse] = useMemo(() => {
    const isSelection = 'selectedIds' in courses;

    return isSelection
      ? [courses.selectedIds, null]
      : [[`${courses.activeItem.id}`], courses.activeItem];
  }, [courses]);
  const [selectedAssignmentIds, activeAssignment] = useMemo(() => {
    const isSelection = 'selectedIds' in assignments;
    return isSelection
      ? [assignments.selectedIds, null]
      : [[`${assignments.activeItem.id}`], assignments.activeItem];
  }, [assignments]);
  const selectedSegmentIds = useMemo(
    () => segments?.selectedIds ?? [],
    [segments?.selectedIds],
  );

  const hasSelection =
    students.selectedIds.length > 0 ||
    selectedAssignmentIds.length > 0 ||
    selectedSegmentIds.length > 0 ||
    selectedCourseIds.length > 0;

  const coursesFilters = useMemo(
    () => ({
      h_userid: students.selectedIds,
      assignment_id: selectedAssignmentIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentIds, students.selectedIds],
  );
  const coursesResult = usePaginatedAPIFetch<
    'courses',
    Course[],
    CoursesResponse
  >(
    'courses',
    // If an active course was provided, do not load list of courses
    activeCourse ? null : routes.courses,
    coursesFilters,
  );

  const assignmentFilters = useMemo(
    () => ({
      h_userid: students.selectedIds,
      course_id: selectedCourseIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedCourseIds, students.selectedIds],
  );
  const assignmentsResults = usePaginatedAPIFetch<
    'assignments',
    Assignment[],
    AssignmentsResponse
  >(
    'assignments',
    // If an active assignment was provided, do not load list of assignments
    activeAssignment ? null : routes.assignments,
    assignmentFilters,
  );

  const studentsFilters = useMemo(
    () => ({
      assignment_id: selectedAssignmentIds,
      segment_authority_provided_id: selectedSegmentIds,
      course_id: selectedCourseIds,
      org_public_id: organizationPublicId,
    }),
    [
      organizationPublicId,
      selectedAssignmentIds,
      selectedCourseIds,
      selectedSegmentIds,
    ],
  );
  const studentsResult = usePaginatedAPIFetch<
    'students',
    Student[],
    StudentsResponse
  >('students', routes.students, studentsFilters);

  return (
    <div className="flex gap-2 flex-wrap">
      <PaginatedMultiSelect
        entity="courses"
        data-testid="courses-select"
        result={coursesResult}
        value={selectedCourseIds}
        onChange={newCourseIds =>
          'onChange' in courses
            ? courses.onChange(newCourseIds)
            : newCourseIds.length === 0 && courses.onClear()
        }
        buttonContent={
          activeCourse ? (
            activeCourse.title
          ) : coursesResult.isLoadingFirstPage ? (
            <>...</>
          ) : selectedCourseIds.length === 0 ? (
            <ContentWithBadge
              count={coursesResult.data?.length ?? 0}
              hasMoreItems={coursesResult.hasMorePages}
            >
              All courses
            </ContentWithBadge>
          ) : selectedCourseIds.length === 1 ? (
            (coursesResult.data?.find(c => `${c.id}` === selectedCourseIds[0])
              ?.title ?? '1 course')
          ) : (
            <>{selectedCourseIds.length} courses</>
          )
        }
        activeItem={activeCourse}
        renderOption={(course, elementRef) => (
          <MultiSelect.Option
            key={course.id}
            value={`${course.id}`}
            elementRef={elementRef}
          >
            <TruncatedText>{course.title}</TruncatedText>
          </MultiSelect.Option>
        )}
      />
      <PaginatedMultiSelect
        entity="assignments"
        data-testid="assignments-select"
        result={assignmentsResults}
        value={selectedAssignmentIds}
        onChange={newAssignmentIds =>
          'onChange' in assignments
            ? assignments.onChange(newAssignmentIds)
            : newAssignmentIds.length === 0 && assignments.onClear()
        }
        buttonContent={
          activeAssignment ? (
            activeAssignment.title
          ) : assignmentsResults.isLoadingFirstPage ? (
            <>...</>
          ) : selectedAssignmentIds.length === 0 ? (
            <ContentWithBadge
              count={assignmentsResults.data?.length ?? 0}
              hasMoreItems={assignmentsResults.hasMorePages}
            >
              All assignments
            </ContentWithBadge>
          ) : selectedAssignmentIds.length === 1 ? (
            (assignmentsResults.data?.find(
              a => `${a.id}` === selectedAssignmentIds[0],
            )?.title ?? '1 assignment')
          ) : (
            <>{selectedAssignmentIds.length} assignments</>
          )
        }
        activeItem={activeAssignment}
        renderOption={(assignment, elementRef) => (
          <AssignmentOption
            key={assignment.id}
            assignment={assignment}
            elementRef={elementRef}
          />
        )}
      />
      {segments && <SegmentsMultiSelect segments={segments} />}
      <PaginatedMultiSelect
        entity="students"
        data-testid="students-select"
        result={studentsResult}
        value={students.selectedIds}
        onChange={newStudentIds => students.onChange(newStudentIds)}
        buttonContent={
          studentsResult.isLoadingFirstPage ? (
            <>...</>
          ) : students.selectedIds.length === 0 ? (
            <ContentWithBadge
              count={studentsResult.data?.length ?? 0}
              hasMoreItems={studentsResult.hasMorePages}
            >
              All students
            </ContentWithBadge>
          ) : students.selectedIds.length === 1 ? (
            (studentsResult.data?.find(
              s => s.h_userid === students.selectedIds[0],
            )?.display_name ?? '1 student')
          ) : (
            <>{students.selectedIds.length} students</>
          )
        }
        renderOption={(student, elementRef) => (
          <StudentOption
            key={student.lms_id}
            student={student}
            elementRef={elementRef}
          />
        )}
      />
      {hasSelection && onClearSelection && (
        <LinkButton
          variant="text-light"
          classes="ml-2 font-bold gap-x-1"
          onClick={() => onClearSelection()}
          data-testid="clear-button"
        >
          <FilterClearIcon />
          Clear filters
        </LinkButton>
      )}
    </div>
  );
}
