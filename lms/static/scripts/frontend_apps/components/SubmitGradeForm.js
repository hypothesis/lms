import { createElement } from 'preact';
import classNames from 'classnames';
import propTypes from 'prop-types';
import { useEffect, useState, useRef } from 'preact/hooks';

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 */

export default function SubmitGradeForm({
  disabled,
  onSubmitGrade,
  studentGrade,
  gradeSaved,
}) {
  const [grade, setGrade] = useState(''); // Current value of the input field.
  const [showError, setShowError] = useState(false); // Is there a validation error message to show?
  const [gradeErrorMessage, setGradeErrorMessage] = useState(''); // The actual validation error message.

  useEffect(() => {
    // Keep track of a private state var for the current grade. Note, this is
    // different than the prop grade from the server.
    setGrade(studentGrade);
  }, [studentGrade]);

  // Used to handle keyboard input effects.
  const refInput = useRef(null);

  /**
   * Coerce the value from the input field to an numeric value.
   * If the value can't be properly cast, then it will remain a string.
   *
   * @param {string} value
   */
  const translatedValue = value => {
    if (value.toString().trim().length === 0) {
      // don't translate a string with only tabs or spaces
      return value;
    }
    const translated = Number(value);
    if (isNaN(translated)) {
      return value;
    } else {
      return translated;
    }
  };

  /**
   * The validator will ensure the value is:
   * - a numeric type
   * - between or equal to a range limit of [0 - 10]
   * -
   * @param {any} value
   */
  const validateNumber = value => {
    if (typeof value !== 'number') {
      setShowError(true);
      setGradeErrorMessage('Grade must be a valid number');
      return false;
    } else if (value < 0 || value > 10) {
      setShowError(true);
      setGradeErrorMessage('Grade must be between 0 and 10');
      return false;
    } else {
      setShowError(false);
      return true;
    }
  };

  /**
   * Validate the grade. If it passes, then send it to `onSubmitGrade`
   *
   * @param {Object} event
   */
  const submitGrade = async event => {
    event.preventDefault();
    if (validateNumber(grade)) {
      onSubmitGrade(grade);
    }
  };

  /**
   * Handles any keyboard input on the grade field.
   *
   * @param {Object} event
   */
  const handleKeyDown = e => {
    // If they key is any key, pass along to handleGradeChange
    if (e.key !== 'Enter') {
      // TODO: some sort of better throttle / debounce
      setTimeout(() => {
        // When the user makes any change to the grade input field, clear
        // out the validation error and update the local grade.
        const value = translatedValue(refInput.current.value);
        setShowError(false);
        setGrade(value);
      }, 50);
    }
  };

  /**
   * Closes the validation error message.
   */
  const closeValidationError = () => {
    setShowError(false);
  };

  // If the grade has not change, then the submit button will remain disabled
  let gradeChanged;
  if (studentGrade !== grade) {
    gradeChanged = true;
  } else {
    gradeChanged = false;
  }

  // Disable the input and the submit button if the `disabled` prop is true,
  // or if the grade does not change, then disable just the submit button.
  const submitProps = {
    disabled: disabled || !gradeChanged,
  };
  const gradeProps = {
    disabled: disabled,
  };

  const errorClass = classNames('SubmitGradeForm__validation-error', {
    'SubmitGradeForm__validation-error--open': showError,
    'SubmitGradeForm__validation-error--close': !showError,
  });

  return (
    <form className="SubmitGradeForm" autoComplete="off">
      <div onClick={closeValidationError} className={errorClass}>
        {gradeErrorMessage}
      </div>
      <label htmlFor="lms-grade">Grade (Out of 10)</label>
      <input
        {...gradeProps}
        id="lms-grade"
        ref={refInput}
        onKeyDown={handleKeyDown}
        type="input"
        defaultValue={grade}
        className={gradeSaved ? 'SubmitGradeForm--grade-saved' : ''}
      />
      <button {...submitProps} onClick={submitGrade} value="what" type="submit">
        <img src="/static/images/check.svg" /> Submit Grade
      </button>
    </form>
  );
}

SubmitGradeForm.propTypes = {
  // Callback to save the grade to the server.
  onSubmitGrade: propTypes.func.isRequired,
  // Disables the the entire form.
  disabled: propTypes.bool,
  // Grade for the current student. (Loaded from the server)
  studentGrade: propTypes.number.isRequired,
  // Renders a quick animation to show it was recently saved.
  gradeSaved: propTypes.bool,
};
