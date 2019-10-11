import { createElement } from 'preact';
import propTypes from 'prop-types';
import { useContext, useEffect, useState, useRef } from 'preact/hooks';

import { Config } from '../config';
import { submitGrade } from '../utils/grader-service';
import { formatToNumber, validateGrade } from '../utils/validation';
import ErrorDialog from './ErrorDialog';
import Spinner from './Spinner';
import ValidationMessage from './ValidationMessage';

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 */

export default function SubmitGradeForm({ disabled, student }) {
  // for validation
  const [showError, setShowError] = useState(false); // Is there a validation error message to show?
  const [gradeErrorMessage, setGradeErrorMessage] = useState(''); // The actual validation error message.
  // for fetching
  const [networkError, setNetworkError] = useState(''); // if there is an error when submitting grade
  const [requestStatus, setRequestStatus] = useState(''); // ajax request state, one of ('', 'fetching', 'error', 'done')

  const { authToken } = useContext(Config);

  useEffect(() => {
    setRequestStatus(''); // clear out network status
  }, [student]);

  // Used to handle keyboard input effects.
  const refInput = useRef(null);

  /**
   * Validate the grade and if it passes, then submit the grade to to `onSubmitGrade`
   *
   * @param {Object} event
   */
  const onSubmitGrade = async event => {
    event.preventDefault();
    const value = formatToNumber(refInput.current.value);
    const validationError = validateGrade(value);

    if (validationError) {
      setGradeErrorMessage(validationError);
      setShowError(true);
    } else {
      try {
        setRequestStatus('fetching');
        // divide value by 10
        await submitGrade({ student, grade: value / 10, authToken });
        setRequestStatus('done');
      } catch (e) {
        setRequestStatus('error');
        setNetworkError(e.errorMessage ? e.errorMessage : 'Unknown error');
      }
    }
  };

  /**
   * If any input is detected, close the validation error message.
   */
  const handleKeyDown = () => {
    setShowError(false);
  };

  return (
    <form className="SubmitGradeForm" autoComplete="off">
      <ValidationMessage
        message={gradeErrorMessage}
        open={showError}
        onClose={() => {
          // Sync up the state when the validator is closed
          setShowError(false);
        }}
      />
      <label htmlFor="lms-grade">Grade (Out of 10)</label>
      <input
        disabled={disabled}
        id="lms-grade"
        ref={refInput}
        onKeyDown={handleKeyDown}
        type="input"
        defaultValue={''}
        className={
          requestStatus === 'done' ? 'SubmitGradeForm--grade-saved' : ''
        }
        key={student.LISResultSourcedId}
      />
      <button
        disabled={disabled}
        onClick={onSubmitGrade}
        value="what"
        type="submit"
      >
        <img src="/static/images/check.svg" /> Submit Grade
      </button>
      {requestStatus === 'error' && (
        <ErrorDialog
          title="Error"
          error={{ message: networkError }}
          onCancel={() => {
            setRequestStatus('');
          }}
        />
      )}
      {requestStatus === 'fetching' && (
        <div className="SubmitGradeForm__loading-backdrop">
          <Spinner className="SubmitGradeForm__spinner" />
        </div>
      )}
    </form>
  );
}

SubmitGradeForm.propTypes = {
  // Disables the the entire form.
  disabled: propTypes.bool,
  // Grade for the current student. (Loaded from the server)
  student: propTypes.object.isRequired,
};
