import {
  Button,
  CancelIcon,
  IconButton,
  MultiSelect,
  RefreshIcon,
} from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import type { MutableRef } from 'preact/hooks';
import { useMemo, useRef } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type {
  Assignment,
  AssignmentsResponse,
  Course,
  CoursesResponse,
  Student,
  StudentsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import type { PaginatedFetchResult } from '../../utils/api';
import { usePaginatedAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';

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

export type DashboardActivityFiltersProps = {
  courses: ActivityFilterSelection | ActivityFilterItem<Course>;
  assignments: ActivityFilterSelection | ActivityFilterItem<Assignment>;
  students: ActivityFilterSelection;
  onClearSelection?: () => void;
};

/**
 * Checks if provided element's scroll is at the bottom.
 * @param offset - Return true if the difference between the element's current
 *                 and maximum scroll position is below this value.
 *                 Defaults to 20.
 */
function elementScrollIsAtBottom(element: HTMLElement, offset = 20): boolean {
  const distanceToTop = element.scrollTop + element.clientHeight;
  const triggerPoint = element.scrollHeight - offset;
  return distanceToTop >= triggerPoint;
}

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
        {assignment.title}
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
      <span
        className={hasDisplayName ? undefined : 'italic'}
        title={hasDisplayName ? undefined : `User ID: ${student.lms_id}`}
        data-testid="option-content-wrapper"
      >
        {displayName}
      </span>
    </MultiSelect.Option>
  );
}

type FiltersEntity = 'courses' | 'assignments' | 'students';

/**
 * Placeholder to indicate a loading is in progress in one of the dropdowns
 */
function LoadingOption({ entity }: { entity: FiltersEntity }) {
  return (
    <div
      className="py-2 px-4 mb-1 text-grey-4 italic"
      data-testid={`loading-more-${entity}`}
    >
      Loading more {entity}...
    </div>
  );
}

type LoadingErrorProps = {
  entity: FiltersEntity;
  retry: () => void;
};

/**
 * Indicates an error occurred while loading filters, and presents a button to
 * retry.
 */
function LoadingError({ entity, retry }: LoadingErrorProps) {
  return (
    <div
      className="flex gap-2 items-center py-2 pl-4 pr-2.5 mb-1"
      data-testid={`${entity}-error`}
      // Make this element "focusable" so that clicking on it does not cause
      // the listbox containing it to be closed
      tabIndex={-1}
    >
      <span className="italic text-red-error">Error loading {entity}</span>
      <Button icon={RefreshIcon} onClick={retry} size="sm">
        Retry
      </Button>
    </div>
  );
}

type PaginatedMultiSelectProps<TResult, TSelect> = {
  result: PaginatedFetchResult<NonNullable<TResult>[]>;
  activeItem?: TResult;
  renderOption: (
    item: NonNullable<TResult>,
    ref?: MutableRef<HTMLElement | null>,
  ) => ComponentChildren;
  entity: FiltersEntity;
  buttonContent?: ComponentChildren;
  value: TSelect[];
  onChange: (newValue: TSelect[]) => void;
};

/**
 * A MultiSelect whose data is fetched from a paginated API.
 * It includes loading and error indicators, and transparently loads more data
 * while scrolling.
 */
function PaginatedMultiSelect<TResult, TSelect>({
  result,
  activeItem,
  entity,
  renderOption,
  buttonContent,
  value,
  onChange,
}: PaginatedMultiSelectProps<TResult, TSelect>) {
  const lastOptionRef = useRef<HTMLElement | null>(null);

  return (
    <MultiSelect
      disabled={result.isLoadingFirstPage}
      value={value}
      onChange={onChange}
      aria-label={`Select ${entity}`}
      containerClasses="!w-auto min-w-[180px]"
      buttonContent={buttonContent}
      data-testid={`${entity}-select`}
      onListboxScroll={e => {
        if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
          result.loadNextPage();
        }
      }}
    >
      <MultiSelect.Option
        value={undefined}
        elementRef={
          !activeItem && (!result.data || result.data.length === 0)
            ? lastOptionRef
            : undefined
        }
      >
        All {entity}
      </MultiSelect.Option>
      {activeItem ? (
        renderOption(activeItem, lastOptionRef)
      ) : (
        <>
          {result.data?.map((item, index, list) =>
            renderOption(
              item,
              list.length - 1 === index ? lastOptionRef : undefined,
            ),
          )}
          {result.isLoading && <LoadingOption entity={entity} />}
          {result.error && (
            <LoadingError
              entity={entity}
              retry={() => {
                // Focus last option before retrying, to avoid the listbox to
                // be closed:
                // - Starting the fetch retry will cause the result to no
                //   longer be in the error state, hence the Retry button will
                //   be umounted.
                // - If the retry button had focus when unmounted, the focus
                //   would revert to the document body.
                // - Since the body is outside the select dropdown, this would
                //   cause the select dropdown to auto-close.
                // - To avoid this we focus a different element just before
                //   initiating the retry.
                lastOptionRef.current?.focus();
                result.retry();
              }}
            />
          )}
        </>
      )}
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

  const hasSelection =
    students.selectedIds.length > 0 ||
    selectedAssignmentIds.length > 0 ||
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
      course_id: selectedCourseIds,
      org_public_id: organizationPublicId,
    }),
    [organizationPublicId, selectedAssignmentIds, selectedCourseIds],
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
            <>All courses</>
          ) : selectedCourseIds.length === 1 ? (
            coursesResult.data?.find(c => `${c.id}` === selectedCourseIds[0])
              ?.title ?? '1 course'
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
            {course.title}
          </MultiSelect.Option>
        )}
      />
      <PaginatedMultiSelect
        entity="assignments"
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
            <>All assignments</>
          ) : selectedAssignmentIds.length === 1 ? (
            assignmentsResults.data?.find(
              a => `${a.id}` === selectedAssignmentIds[0],
            )?.title ?? '1 assignment'
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
      <PaginatedMultiSelect
        entity="students"
        result={studentsResult}
        value={students.selectedIds}
        onChange={newStudentIds => students.onChange(newStudentIds)}
        buttonContent={
          studentsResult.isLoadingFirstPage ? (
            <>...</>
          ) : students.selectedIds.length === 0 ? (
            <>All students</>
          ) : students.selectedIds.length === 1 ? (
            studentsResult.data?.find(
              s => s.h_userid === students.selectedIds[0],
            )?.display_name ?? '1 student'
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
        <IconButton
          title="Clear filters"
          icon={CancelIcon}
          classes="text-grey-7"
          onClick={() => onClearSelection()}
          data-testid="clear-button"
        />
      )}
    </div>
  );
}
