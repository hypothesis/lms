import { createElement } from 'preact';
import classNames from 'classnames';
import { useContext, useEffect, useState, useRef } from 'preact/hooks';
import propTypes from 'prop-types';

import { Config } from '../config';
import ErrorDialog from './ErrorDialog';
import Spinner from './Spinner';
import SvgIcon from './SvgIcon';
import { fetchGrade, submitGrade } from '../utils/grader-service';
import { trustMarkup } from '../utils/trusted';
import { formatToNumber, validateGrade } from '../utils/validation';
import ValidationMessage from './ValidationMessage';

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 */

export default function SubmitGradeForm({ disabled = false, student }) {
  const [showError, setShowError] = useState(false); // Is there a validation error message to show?
  const [gradeErrorMessage, setGradeErrorMessage] = useState(''); // The actual validation error message.
  const [grade, setGrade] = useState('');

  const [networkError, setNetworkError] = useState(''); // If there is an error when submitting grade
  const [requestStatus, setRequestStatus] = useState(''); // Ajax request state, one of ('', 'fetching', 'error', 'done')
  const [fetchStatus, setFetchStatus] = useState(''); // Ajax request state, one of ('', 'fetching', 'error', 'done')

  const { authToken } = useContext(Config);

  // Used to handle keyboard input effects.
  const refInput = useRef(null);

  useEffect(() => {
    setRequestStatus(''); // clear out network status

    // Fetch the grade from the service api
    let fetchedGradeDone = false; // flag to prevent updating more than once
    if (Object.entries(student).length) {
      // See https://github.com/facebook/react/issues/14326 for async in useEffect
      (async () => {
        try {
          setFetchStatus('fetching');
          setGrade(''); // Clear the older grade so we don't show the wrong grade with the new student
          const response = await fetchGrade({ student, authToken });
          setFetchStatus('done');
          if (!fetchedGradeDone) {
            // Ignore if we started fetching something else
            setGrade(response.currentScore * 10); // Scale the grade to be [0-10], grade is saved as a value between [0-1]
          }
        } catch (e) {
          setNetworkError(e.errorMessage ? e.errorMessage : 'Unknown error');
          setFetchStatus('error');
        }
      })();
    } else {
      setGrade(''); // No valid student, clear grade
    }
    return () => {
      fetchedGradeDone = true;
    };
  }, [student, authToken]);

  /**
   * Validate the grade and if it passes, then submit the grade to to `onSubmitGrade`
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
        // Divide value by 10 because the lms service layer expects grade to be a value between [0-1] but
        // we treat this on the UI to be between [0-10].
        await submitGrade({ student, grade: value / 10, authToken });
        setRequestStatus('done');
      } catch (e) {
        setNetworkError(e.errorMessage ? e.errorMessage : 'Unknown error');
        setRequestStatus('error');
      }
    }
  };

  /**
   * If any input is detected, close the ValidationMessage.
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
          // Sync up the state when the ValidationMessage is closed
          setShowError(false);
        }}
      />
      <label className="SubmitGradeForm__label" htmlFor="lms-grade">
        Grade (Out of 10)
      </label>
      <span className="SubmitGradeForm__grade-wrapper">
        <input
          className={classNames('SubmitGradeForm__grade', {
            'SubmitGradeForm__grade--saved': requestStatus === 'done',
          })}
          disabled={disabled}
          id="lms-grade"
          ref={refInput}
          onKeyDown={handleKeyDown}
          type="input"
          defaultValue={grade}
          key={grade}
        />
        <Spinner
          className={classNames('SubmitGradeForm__fetch-spinner', {
            'SubmitGradeForm__fetch-spinner--active':
              fetchStatus === 'fetching',
            'SubmitGradeForm__fetch-spinner--fade-away': fetchStatus === 'done',
          })}
        />
      </span>
      <button
        className="SubmitGradeForm__submit"
        disabled={disabled}
        onClick={onSubmitGrade}
        type="submit"
      >
        <SvgIcon
          className="SubmitGradeForm__check-icon"
          src={trustMarkup(require('../../../images/check.svg'))}
          inline="true"
        />{' '}
        Submit Grade
      </button>
      {(requestStatus === 'error' || fetchStatus === 'error') && (
        <ErrorDialog
          title="Error"
          error={{ message: networkError }}
          onCancel={() => {
            setRequestStatus('');
            setFetchStatus('');
          }}
        />
      )}
      {requestStatus === 'fetching' && (
        <div className="SubmitGradeForm__loading-backdrop">
          <Spinner className="SubmitGradeForm__submit-spinner" />
        </div>
      )}
    </form>
  );
}

SubmitGradeForm.propTypes = {
  // Disables the the entire form.
  disabled: propTypes.bool,
  // Grade for the current student.SubmitGradeForm.propTypes
  student: propTypes.object.isRequired,
};
