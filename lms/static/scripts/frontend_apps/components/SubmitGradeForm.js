import { createElement } from 'preact';
import classNames from 'classnames';
import {
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
  useRef,
} from 'preact/hooks';
import propTypes from 'prop-types';

import { Config } from '../config';
import ErrorDialog from './ErrorDialog';
import Spinner from './Spinner';
import SvgIcon from './SvgIcon';
import { fetchGrade, submitGrade } from '../utils/grader-service';
import { useUniqueId } from '../utils/hooks';
import { formatToNumber, scaleGrade, validateGrade } from '../utils/validation';
import ValidationMessage from './ValidationMessage';

// Grades are always stored as a value between [0-1] on the service layer.
// Scale the grade to [0-10] when loading it into the UI and scale it
// back to [0-1] when saving it to the api service.
const GRADE_MULTIPLIER = 10;

/**
 * Custom useEffect function that handles fetching a student's
 * grade and returning the result of that grade and the loading
 * and error status of that fetch request.
 */
const useFetchGrade = student => {
  const {
    api: { authToken },
  } = useContext(Config);
  const [grade, setGrade] = useState('');
  const [gradeLoading, setGradeLoading] = useState(false);

  useEffect(() => {
    let didCancel;
    // Don't bother fetching a grade if the student object is empty
    if (Object.entries(student).length) {
      // Fetch the grade from the service api
      // See https://www.robinwieruch.de/react-hooks-fetch-data for async in useEffect
      const fetchData = async () => {
        setGradeLoading(true);
        setGrade(''); // Clear previous grade so we don't show the wrong grade with the new student

        const response = await fetchGrade({ student, authToken });
        if (!didCancel) {
          // Only set these values if we didn't cancel this request
          if (response.currentScore) {
            setGrade(scaleGrade(response.currentScore, GRADE_MULTIPLIER));
          }
          setGradeLoading(false);
        }
      };
      fetchData();
    } else {
      // If there is no valid student, don't show a grade
      setGrade('');
    }
    // Called when unmounting the component
    return () => {
      // Set a flag to cancel the the fetchGrade response from saving to state
      didCancel = true;
    };
  }, [student, authToken]);
  return { grade, gradeLoading };
};

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 */

export default function SubmitGradeForm({ disabled = false, student }) {
  // State for loading the grade
  const { grade, gradeLoading } = useFetchGrade(student);

  // The following is state for saving the grade
  //
  // If there is an error when submitting a grade?
  const [submitGradeError, setSubmitGradeError] = useState('');
  // Is set to true when the grade is being currently posted to the service
  const [gradeSaving, setGradeSaving] = useState(false);
  // Changes the input field's background to green for a short duration when true
  const [gradeSaved, setGradeSaved] = useState(false);

  // The following is state for local validation errors
  //
  // Is there a validation error message to show?
  const [showValidationError, setValidationError] = useState(false);
  // The actual validation error message.
  const [validationMessage, setValidationMessageMessage] = useState('');
  // Unique id attribute for <input>
  const gradeId = useUniqueId('SubmitGradeForm__grade:');

  const {
    api: { authToken },
  } = useContext(Config);

  // Used to handle keyboard input changes for the grade input field.
  const inputRef = useRef(/** @type {HTMLInputElement|null} */ (null));

  // Clear the previous grade saved status when the user changes.
  useEffect(() => {
    setGradeSaved(false);
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current.focus();
    inputRef.current.select();
  }, [grade]);

  /**
   * Validate the grade and if it passes, then submit the grade to to `onSubmitGrade`
   */
  const onSubmitGrade = async event => {
    event.preventDefault();
    const value = formatToNumber(inputRef.current.value);
    const validationError = validateGrade(value);

    if (validationError) {
      setValidationMessageMessage(validationError);
      setValidationError(true);
    } else {
      setGradeSaving(true);
      try {
        await submitGrade({
          student,
          grade: value / GRADE_MULTIPLIER,
          authToken,
        });
        setGradeSaved(true);
      } catch (e) {
        setSubmitGradeError(e.errorMessage ? e.errorMessage : 'Unknown error');
      }
      setGradeSaving(false);
    }
  };

  /**
   * If any input is detected, close the ValidationMessage.
   */
  const handleKeyDown = () => {
    setValidationError(false);
    setGradeSaved(false);
  };

  return (
    <form className="SubmitGradeForm" autoComplete="off">
      {validationMessage && (
        <ValidationMessage
          message={validationMessage}
          open={showValidationError}
          onClose={() => {
            // Sync up the state when the ValidationMessage is closed
            setValidationError(false);
          }}
        />
      )}
      <label className="SubmitGradeForm__label" htmlFor={gradeId}>
        Grade (Out of 10)
      </label>
      <span className="SubmitGradeForm__grade-wrapper">
        <input
          className={classNames('SubmitGradeForm__grade', {
            'is-saved': gradeSaved,
          })}
          disabled={disabled}
          id={gradeId}
          ref={inputRef}
          onInput={handleKeyDown}
          type="input"
          // @ts-expect-error - `defaultValue` is missing from `<input>` prop types.
          defaultValue={grade}
          key={student.LISResultSourcedId}
        />
        <Spinner
          className={classNames('SubmitGradeForm__fetch-spinner', {
            'is-active': gradeLoading,
            'is-fade-away': !gradeLoading && student.LISResultSourcedId,
          })}
        />
      </span>
      <button
        type="submit"
        className="SubmitGradeForm__submit"
        disabled={disabled}
        onClick={onSubmitGrade}
      >
        <SvgIcon
          className="SubmitGradeForm__check-icon"
          name="check"
          inline={true}
        />{' '}
        Submit Grade
      </button>
      {!!submitGradeError && (
        <ErrorDialog
          title="Error"
          error={{ message: submitGradeError }}
          onCancel={() => {
            setSubmitGradeError('');
          }}
        />
      )}
      {gradeSaving && (
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
