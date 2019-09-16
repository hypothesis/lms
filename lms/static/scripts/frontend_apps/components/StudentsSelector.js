import { createElement } from 'preact';
import propTypes from 'prop-types';

/**
 * A student navigation tool which shows an active student select list and a previous and next button to
 * switch students.
 *
 * WIP component.
 */

export default function StudentsSelector({
  onSelectStudent,
  selectedStudentIndex,
  students,
}) {
  // Disable the next button if at the end of the list
  const hasNextStudent = selectedStudentIndex + 1 < students.length;
  // Disable the previous button if at the start of the list
  const hasPrevStudent = selectedStudentIndex > 0;

  /**
   * Select the next student in the list
   */
  const onNextStudent = () => {
    if (selectedStudentIndex + 1 < students.length) {
      onSelectStudent(selectedStudentIndex + 1);
    }
  };
  /**
   * Select the previous student in the list
   */
  const onPrevStudent = () => {
    if (selectedStudentIndex > 0) {
      onSelectStudent(selectedStudentIndex - 1);
    }
  };

  /**
   * Build the <select> list from the current array of students
   */
  const studentList = () => {
    const options = students.map((student, i) => {
      return (
        <option
          key={`student-${i}`}
          selected={selectedStudentIndex === i}
          value={i}
        >
          {student.displayName}
        </option>
      );
    });
    return (
      <select
        onChange={e => {
          onSelectStudent(e.target.selectedIndex);
        }}
      >
        {options}
      </select>
    );
  };

  return (
    <div className="StudentsSelector">
      <button
        aria-label="previous student"
        disabled={!hasPrevStudent}
        onClick={onPrevStudent}
      >
        <img src="/static/images/iconmonstr-arrow-left-thin.svg" />
      </button>
      <div className="StudentsSelector__student">{studentList()}</div>
      <button
        aria-label="next student"
        disabled={!hasNextStudent}
        onClick={onNextStudent}
      >
        <img src="static/images/iconmonstr-arrow-right-thin.svg" />
      </button>
    </div>
  );
}

StudentsSelector.propTypes = {
  // Callback when the selected student changes
  onSelectStudent: propTypes.func.isRequired,

  // Students array and selected index of that array
  selectedStudentIndex: propTypes.number.isRequired,
  students: propTypes.array.isRequired,
};
