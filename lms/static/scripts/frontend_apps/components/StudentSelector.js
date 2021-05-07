import { SvgIcon, IconButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';

/**
 * @typedef Student
 * @prop {string} displayName
 */

/**
 * @typedef StudentSelectorProps
 * @prop {(index: number) => any} onSelectStudent -
 *   Callback invoked when the selected student changes
 * @prop {number} selectedStudentIndex -
 *   Index of selected student in `students` or -1 if no student is selected
 * @prop {Student[]} students - Ordered list of students to display in the drop-down
 */

/**
 * A student navigation tool which shows a student selection list and a previous and next button.
 *
 * @param {StudentSelectorProps} props
 */
export default function StudentSelector({
  onSelectStudent,
  selectedStudentIndex,
  students,
}) {
  // Disable the next button if at the end of the list. The length is equal to
  // the student list plus the default "All Students" option.
  const hasNextView = selectedStudentIndex + 1 < students.length;
  // Disable the previous button only if the selectedStudentIndex is less than 0
  // indicating the "All Students" choice is selected.
  const hasPrevView = selectedStudentIndex >= 0;

  /**
   * Select the next student index in the list.
   */
  const onNextView = () => {
    onSelectStudent(selectedStudentIndex + 1);
  };
  /**
   * Select the previous student index in the list. The 0 index
   * represents "All Students."
   */
  const onPrevView = () => {
    onSelectStudent(selectedStudentIndex - 1);
  };

  /**
   * Build the <select> list from the current array of students.
   */
  const buildStudentList = () => {
    const options = students.map((student, i) => (
      <option
        key={`student-${i}`}
        selected={selectedStudentIndex === i}
        value={i}
      >
        {student.displayName}
      </option>
    ));
    options.unshift(
      <option
        key={'all-students'}
        selected={selectedStudentIndex === -1}
        value={-1}
      >
        All Students
      </option>
    );

    return (
      <span className="StudentsSelector__students">
        {/*
        This lint issue may have arisen from browser inconsistency issues with
        `onChange` which have since been fixed. See browser compatibility note here:
        https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event#annotations:xeC6ClQsEequhUdih2lXzw
        */}
        {/* eslint-disable-next-line jsx-a11y/no-onchange*/}
        <select
          className="StudentsSelector__students-select"
          onChange={e => {
            onSelectStudent(
              parseInt(/** @type {HTMLInputElement} */ (e.target).value)
            );
          }}
        >
          {options}
        </select>
        <SvgIcon
          className="StudentsSelector__students-icon"
          name="caret-down"
          inline={true}
        />{' '}
      </span>
    );
  };

  return (
    <div className="StudentSelector">
      <span className="StudentSelector__button">
        <IconButton
          className="InputButton--left"
          icon="arrow-left"
          disabled={!hasPrevView}
          onClick={onPrevView}
          title="Previous Student"
        />
      </span>
      {buildStudentList()}
      <span className="StudentSelector__button">
        <IconButton
          className="InputButton--right"
          icon="arrow-right"
          disabled={!hasNextView}
          onClick={onNextView}
          title="Next Student"
        />
      </span>
    </div>
  );
}
