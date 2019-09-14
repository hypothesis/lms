import { createElement } from 'preact';
import propTypes from 'prop-types';

/**
 * A student navigation tool which shows an active student and a previous and next button to
 * switch the student.
 *
 * This is component is still a WIP.
 */

export default function StudentsSelector({
  // booleans
  hasPrevStudent,
  hasNextStudent,
  // onclick callbacks
  onPrevStudent,
  onNextStudent,
  // student object
  student,
}) {
  return (
    <div className="StudentsSelector">
      <button
        aria-label="previous student"
        disabled={!hasPrevStudent}
        onClick={onPrevStudent}
      >
        <img src="/static/images/iconmonstr-arrow-left-thin.svg" />
      </button>
      <div className="StudentsSelector__student">
        <span>{student.name}</span>
      </div>
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
  onPrevStudent: propTypes.func.isRequired,
  onNextStudent: propTypes.func.isRequired,

  /* Are we at the start of the list*/
  hasPrevStudent: propTypes.boolean,
  /* Are we at the emd of the list*/
  hasNextStudent: propTypes.boolean,

  student: propTypes.object.isRequired,
};
