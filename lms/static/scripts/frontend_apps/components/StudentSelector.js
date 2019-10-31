import { createElement } from 'preact';
import propTypes from 'prop-types';

import SvgIcon from './SvgIcon';
import { trustMarkup } from '../utils/trusted';

/**
 * A student navigation tool which shows a student selection list and a previous and next button.
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
        <select
          className="StudentsSelector__students-select"
          onChange={e => {
            onSelectStudent(parseInt(e.target.value));
          }}
        >
          {options}
        </select>
        <SvgIcon
          className="StudentsSelector__students-icon"
          src={trustMarkup(require('../../../images/caret-down.svg'))}
          inline="true"
        />{' '}
      </span>
    );
  };

  return (
    <div className="StudentSelector">
      <button
        className="StudentSelector-change-student"
        aria-label="previous student"
        disabled={!hasPrevView}
        onClick={onPrevView}
      >
        <SvgIcon
          className="StudentSelector-change-student-svg"
          src={trustMarkup(require('../../../images/arrow-left.svg'))}
          inline="true"
        />
      </button>
      {buildStudentList()}
      <button
        className="StudentSelector-change-student"
        aria-label="next student"
        disabled={!hasNextView}
        onClick={onNextView}
      >
        <SvgIcon
          className="StudentSelector-change-student-svg"
          src={trustMarkup(require('../../../images/arrow-right.svg'))}
          inline="true"
        />
      </button>
    </div>
  );
}

StudentSelector.propTypes = {
  // Callback when the selected student changes.
  onSelectStudent: propTypes.func.isRequired,

  // Students array and selected index of that array.
  selectedStudentIndex: propTypes.number.isRequired,
  students: propTypes.array.isRequired,
};
