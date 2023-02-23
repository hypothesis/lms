import {
  Button,
  CheckIcon,
  Input,
  Spinner,
  SpinnerOverlay,
} from '@hypothesis/frontend-shared/lib/next';
import classnames from 'classnames';
import { useEffect, useLayoutEffect, useState, useRef } from 'preact/hooks';

import type { StudentInfo } from '../config';
import type { ErrorLike } from '../errors';
import { useService, GradingService } from '../services';
import { useFetch } from '../utils/fetch';
import { useUniqueId } from '../utils/hooks';
import { formatToNumber, scaleGrade, validateGrade } from '../utils/validation';

import ErrorModal from './ErrorModal';
import ValidationMessage from './ValidationMessage';

// Grades are always stored as a value between [0-1] on the service layer.
// Scale the grade to [0-10] when loading it into the UI and scale it
// back to [0-1] when saving it to the api service.
const GRADE_MULTIPLIER = 10;

export type SubmitGradeFormProps = {
  student: StudentInfo | null;
};

/**
 * A form with a single input field and submit button for an instructor to
 * save a student's grade.
 */
export default function SubmitGradeForm({ student }: SubmitGradeFormProps) {
  const [fetchGradeErrorDismissed, setFetchGradeErrorDismissed] =
    useState(false);
  const gradingService = useService(GradingService);

  const fetchGrade = async (student: StudentInfo) => {
    setFetchGradeErrorDismissed(false);
    const { currentScore = null } = await gradingService.fetchGrade({
      student,
    });
    return currentScore === null
      ? ''
      : `${scaleGrade(currentScore, GRADE_MULTIPLIER)}`;
  };

  const grade = useFetch(
    student ? `grade:${student.userid}` : null,
    student ? () => fetchGrade(student) : undefined
  );

  // The following is state for saving the grade
  //
  // If there is an error when submitting a grade?
  const [submitGradeError, setSubmitGradeError] = useState<ErrorLike | null>(
    null
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

  // Used to handle keyboard input changes for the grade input field.
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Clear the previous grade saved status when the user changes.
  useEffect(() => {
    setGradeSaved(false);
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current!.focus();
    inputRef.current!.select();
  }, [grade]);

  /**
   * Validate the grade and if it passes, then submit the grade to to `onSubmitGrade`
   */
  const onSubmitGrade = async (event: Event) => {
    event.preventDefault();
    const value = formatToNumber(inputRef.current!.value);
    const validationError = validateGrade(value);

    if (validationError) {
      setValidationMessageMessage(validationError);
      setValidationError(true);
    } else {
      setGradeSaving(true);
      try {
        await gradingService.submitGrade({
          student: student as StudentInfo,
          // nb. `value` will be a number if there was no validation error.
          grade: (value as number) / GRADE_MULTIPLIER,
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
      <form autoComplete="off">
        <label htmlFor={gradeId} className="font-semibold text-xs">
          Grade (Out of 10)
        </label>
        <div className="flex">
          <span className="relative w-14">
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
            <Input
              classes={classnames(
                'text-center',
                'disabled:opacity-50',
                'border border-r-0 rounded-r-none',
                {
                  'animate-gradeSubmitSuccess': gradeSaved,
                }
              )}
              data-testid="grade-input"
              disabled={disabled}
              id={gradeId}
              elementRef={inputRef}
              onInput={handleKeyDown}
              type="text"
              defaultValue={grade.data ?? ''}
              key={student ? student.LISResultSourcedId : null}
            />
            {grade.isLoading && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <Spinner size="md" />
              </div>
            )}
          </span>

          <Button
            icon={CheckIcon}
            type="submit"
            classes={classnames(
              'border rounded-l-none ring-inset',
              'disabled:opacity-50'
            )}
            disabled={disabled}
            onClick={onSubmitGrade}
          >
            Submit Grade
          </Button>
        </div>
        {gradeSaving && <SpinnerOverlay />}
      </form>
      {!!submitGradeError && (
        <ErrorModal
          description="Unable to submit grade"
          error={submitGradeError}
          onCancel={() => {
            setSubmitGradeError(null);
          }}
          cancelLabel="Close"
        />
      )}
      {grade.error && !fetchGradeErrorDismissed && (
        <ErrorModal
          description="Unable to fetch grade"
          error={grade.error}
          cancelLabel="Close"
          onCancel={() => setFetchGradeErrorDismissed(true)}
        />
      )}
    </>
  );
}
