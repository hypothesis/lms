import {
  ArrowLeftIcon,
  ArrowRightIcon,
  IconButton,
  InputGroup,
  Select,
} from '@hypothesis/frontend-shared/lib/next';
import classnames from 'classnames';

export type Student = {
  displayName: string;
};

export type StudentSelectorProps = {
  /** Callback invoked when the selected student changes */
  onSelectStudent: (index: number) => void;
  /** Index of selected student in `students` or -1 if no student is selected */
  selectedStudentIndex: number;
  /** Ordered list of students to display in the drop-down */
  students: Student[];
};

/**
 * A drop-down control that allows selecting a student from a list of students.
 */
export default function StudentSelector({
  onSelectStudent,
  selectedStudentIndex,
  students,
}: StudentSelectorProps) {
  // Disable the next button if at the end of the list. The length is equal to
  // the student list plus the default "All Students" option.
  const hasNextView = selectedStudentIndex + 1 < students.length;
  // Disable the previous button only if the selectedStudentIndex is less than 0
  // indicating the "All Students" choice is selected.
  const hasPrevView = selectedStudentIndex >= 0;

  const onNextView = () => {
    onSelectStudent(selectedStudentIndex + 1);
  };

  const onPrevView = () => {
    onSelectStudent(selectedStudentIndex - 1);
  };

  return (
    <div
      className={classnames(
        // Narrower widths: label above field
        'flex flex-col gap-1',
        // Wider widths: label to left of field
        'xl:flex-row xl:gap-3 xl:items-center'
      )}
    >
      <label
        className={classnames(
          'flex-grow font-medium text-sm leading-none',
          'xl:text-right'
        )}
        data-testid="student-selector-label"
      >
        {selectedStudentIndex >= 0 ? (
          <span>
            Student {`${selectedStudentIndex + 1} of ${students.length}`}
          </span>
        ) : (
          <span>{`${students.length} Students`}</span>
        )}
      </label>
      {/**
       * This <div> is needed as a container because InputGroup establishes a
       * new flex layout. This ensures that this <div>'s contents amount to a
       * single flex-child of the outermost <div> here.
       */}
      <div>
        <InputGroup>
          <IconButton
            icon={ArrowLeftIcon}
            title="Previous student"
            disabled={!hasPrevView}
            onClick={onPrevView}
            variant="dark"
          />
          <Select
            aria-label="Select student"
            classes="xl:w-80"
            onChange={e => {
              onSelectStudent(parseInt((e.target as HTMLInputElement).value));
            }}
          >
            <option
              key={'all-students'}
              selected={selectedStudentIndex === -1}
              value={-1}
            >
              All Students
            </option>
            {students.map((student, i) => (
              <option
                key={`student-${i}`}
                selected={selectedStudentIndex === i}
                value={i}
              >
                {student.displayName}
              </option>
            ))}
          </Select>
          <IconButton
            icon={ArrowRightIcon}
            title="Next student"
            disabled={!hasNextView}
            onClick={onNextView}
            variant="dark"
          />
        </InputGroup>
      </div>
    </div>
  );
}
