import {
  ArrowLeftIcon,
  ArrowRightIcon,
  IconButton,
  InputGroup,
  Select,
} from '@hypothesis/frontend-shared';

import type { StudentInfo } from '../config';
import { useUniqueId } from '../utils/hooks';

export type StudentOption = Pick<StudentInfo, 'displayName'>;

export type StudentSelectorProps<Student> = {
  /**
   * Callback invoked when the selected student changes. Invoked with `null`
   * when the "All students" option is selected.
   */
  onSelectStudent: (student: Student | null) => void;
  selectedStudent: Student | null;
  students: Student[];
};

/**
 * A drop-down control that allows selecting a student from a list of students,
 * with previous and next buttons to select students sequentially from the list.
 *
 * An "All students" option is prepended to the list, representing no selected
 * student.
 */
export default function StudentSelector<Student extends StudentOption>({
  onSelectStudent,
  selectedStudent,
  students,
}: StudentSelectorProps<Student>) {
  const selectedIndex = selectedStudent
    ? students.findIndex(student => student === selectedStudent)
    : -1;
  const hasSelectedStudent = selectedIndex >= 0;
  const selectId = useUniqueId('student-select');

  const onNext = () => {
    onSelectStudent(students[selectedIndex + 1]);
  };

  const onPrevious = () => {
    onSelectStudent(selectedIndex === 0 ? null : students[selectedIndex - 1]);
  };

  const handleSelectStudent = (e: Event) => {
    const studentIndex = parseInt((e.target as HTMLInputElement).value);
    if (studentIndex === -1) {
      onSelectStudent(null);
    } else {
      onSelectStudent(students[studentIndex]);
    }
  };

  return (
    <>
      <label
        className="font-semibold text-xs"
        data-testid="student-selector-label"
        htmlFor={selectId}
      >
        {hasSelectedStudent ? (
          <>
            Student {selectedIndex + 1} of {students.length}
          </>
        ) : (
          <>{students.length} Students</>
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
            data-testid="previous-student-button"
            disabled={!hasSelectedStudent}
            icon={ArrowLeftIcon}
            onClick={onPrevious}
            title="Previous student"
            variant="dark"
          />
          <Select
            classes="min-w-[12rem] xl:w-[20rem]"
            aria-label="Select student"
            id={selectId}
            onChange={handleSelectStudent}
          >
            <option
              key={'student-all'}
              selected={!hasSelectedStudent}
              value={-1}
            >
              All Students
            </option>
            {students.map((studentOption, idx) => (
              <option
                key={`student-${idx}`}
                selected={selectedIndex === idx}
                value={idx}
              >
                {studentOption.displayName}
              </option>
            ))}
          </Select>
          <IconButton
            data-testid="next-student-button"
            disabled={selectedIndex >= students.length - 1}
            icon={ArrowRightIcon}
            onClick={onNext}
            title="Next student"
            variant="dark"
          />
        </InputGroup>
      </div>
    </>
  );
}
