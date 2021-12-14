import {
  FullScreenSpinner,
  LabeledButton,
  Spinner,
} from '@hypothesis/frontend-shared';

import classnames from 'classnames';
import { useEffect, useLayoutEffect, useState, useRef } from 'preact/hooks';

import ErrorDialog from './ErrorDialog';
import { useService, GradingService } from '../services';
import { useUniqueId } from '../utils/hooks';
import { formatToNumber, scaleGrade, validateGrade } from '../utils/validation';
import ValidationMessage from './ValidationMessage';

// Grades are always stored as a value between [0-1] on the service layer.
// Scale the grade to [0-10] when loading it into the UI and scale it
// back to [0-1] when saving it to the api service.
const GRADE_MULTIPLIER = 10;

/**
 * @typedef {import('../config').StudentInfo} StudentInfo
 * @typedef {import('../errors').ErrorLike} ErrorLike
 */

/**
 * Custom useEffect function that handles fetching a student's
 * grade and returning the result of that grade and the loading
 * and error status of that fetch request.
 *
 * @param {StudentInfo|null} student
 * @param {(value: ErrorLike) => void} setFetchGradeError
 */
const useFetchGrade = (student, setFetchGradeError) => {
  const gradingService = useService(GradingService);
  const [grade, setGrade] = useState('');
  const [gradeLoading, setGradeLoading] = useState(false);

  useEffect(() => {
    /** @type {boolean} */
    let ignoreResults;
    if (student) {
      // Fetch the grade from the service api
      // See https://www.robinwieruch.de/react-hooks-fetch-data for async in useEffect
      const fetchData = async () => {
        setGradeLoading(true);
        setGrade(''); // Clear previous grade so we don't show the wrong grade with the new student
        try {
          const { currentScore } = await gradingService.fetchGrade({ student });
          if (!ignoreResults && currentScore) {
            // Only set these values if we didn't cancel this request
            setGrade(scaleGrade(currentScore, GRADE_MULTIPLIER));
          }
        } catch (e) {
          setFetchGradeError(e);
        } finally {
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
      // Set a flag to ignore the the fetchGrade response from saving to state
      ignoreResults = true;
    };
  }, [gradingService, student, setFetchGradeError]);
  return { grade, gradeLoading };
};

/**
 * @typedef SubmitGradeFormProps
 * @prop {StudentInfo|null} student - The student to fetch and submit grades for
 */

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 *
 * @param {SubmitGradeFormProps} props
 */
export default function SubmitGradeForm({ student }) {
  // State for loading the grade
  const [fetchGradeError, setFetchGradeError] = useState(
    /** @type {ErrorLike|null} */ (null)
  );
  const { grade, gradeLoading } = useFetchGrade(student, setFetchGradeError);

  // The following is state for saving the grade
  //
  // If there is an error when submitting a grade?
  const [submitGradeError, setSubmitGradeError] = useState(
    /** @type {ErrorLike|null} */ (null)
  );
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

  const gradingService = useService(GradingService);

  // Used to handle keyboard input changes for the grade input field.
  const inputRef = /** @type {{ current: HTMLInputElement }} */ (useRef());

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
   *
   * @param {Event} event
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
        await gradingService.submitGrade({
          student: /** @type {StudentInfo} */ (student),
          // nb. `value` will be a number if there was no validation error.
          grade: /** @type {number} */ (value) / GRADE_MULTIPLIER,
        });
        setGradeSaved(true);
      } catch (e) {
        setSubmitGradeError(e);
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

  const disabled = !student;

  return (
    <>
      <form
        className={classnames(
          // At narrower width, label above input (columnar)
          'flex flex-col gap-1',
          // At wider width, label left of input (row)
          'xl:flex-row xl:gap-3 xl:items-center'
        )}
        autoComplete="off"
      >
        <label
          htmlFor={gradeId}
          className="flex-grow font-medium text-sm leading-none"
        >
          Grade (Out of 10)
        </label>
        <div className="flex flex-row">
          <span className="relative">
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
            <input
              className={classnames(
                'w-14 h-touch-minimum text-center',
                'disabled:opacity-50',
                'hyp-u-outline-on-keyboard-focus--inset hyp-u-border',
                'border-r-0',
                {
                  'animate-gradeSubmitSuccess': gradeSaved,
                }
              )}
              data-testid="grade-input"
              disabled={disabled}
              id={gradeId}
              ref={inputRef}
              onInput={handleKeyDown}
              type="input"
              // @ts-expect-error - `defaultValue` is missing from `<input>` prop types.
              defaultValue={grade}
              key={student ? student.LISResultSourcedId : null}
            />
            {gradeLoading && <Spinner classes="hyp-u-absolute-centered" />}
          </span>

          <LabeledButton
            icon="check"
            type="submit"
            classes={classnames(
              'h-touch-minimum',
              'disabled:opacity-50 disabled:cursor-default',
              'hyp-u-border hyp-u-outline-on-keyboard-focus--inset'
            )}
            disabled={disabled}
            onClick={onSubmitGrade}
          >
            Submit Grade
          </LabeledButton>
        </div>
        {gradeSaving && <FullScreenSpinner />}
      </form>
      {!!submitGradeError && (
        <ErrorDialog
          description="Unable to submit grade"
          error={submitGradeError}
          onCancel={() => {
            setSubmitGradeError(null);
          }}
          cancelLabel="Close"
        />
      )}
      {!!fetchGradeError && (
        <ErrorDialog
          description="Unable to fetch grade"
          error={fetchGradeError}
          onCancel={() => {
            setFetchGradeError(null);
          }}
          cancelLabel="Close"
        />
      )}
    </>
  );
}
