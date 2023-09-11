import {
  Button,
  CheckIcon,
  Input,
  Spinner,
  SpinnerOverlay,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useEffect,
  useLayoutEffect,
  useState,
  useRef,
  useCallback,
  useMemo,
} from 'preact/hooks';

import type { StudentInfo } from '../config';
import type { ErrorLike } from '../errors';
import { useService, GradingService } from '../services';
import { useFetch } from '../utils/fetch';
import { formatGrade, validateGrade } from '../utils/grade-validation';
import { useUniqueId } from '../utils/hooks';
import { useWarnOnPageUnload } from '../utils/use-warn-on-page-unload';
import ErrorModal from './ErrorModal';
import ValidationMessage from './ValidationMessage';

export type SubmitGradeFormProps = {
  student: StudentInfo | null;

  /**
   * Scaling factor applied to grade values from the LMS to get the values
   * entered by the user. Default value is 10.
   *
   * LTI 1.1 only supports grade values between 0 and 1, which we then rescale
   * to 0-{scoreMaximum} in the UI. LTI 1.3+ offer more flexibility (see [1]).
   *
   * [1] https://www.imsglobal.org/spec/lti-ags/v2p0
   */
  scoreMaximum?: number;

  /** It lets parent components know if there are unsaved changes in the grading form */
  onUnsavedChanges?: (hasUnsavedChanges: boolean) => void;
};

const DEFAULT_MAX_SCORE = 10;

/**
 * A form with a single input field and submit button for an instructor to
 * save a student's grade.
 */
export default function SubmitGradeForm({
  student,
  onUnsavedChanges,
  scoreMaximum = DEFAULT_MAX_SCORE,
}: SubmitGradeFormProps) {
  const [fetchGradeErrorDismissed, setFetchGradeErrorDismissed] =
    useState(false);
  const gradingService = useService(GradingService);

  const fetchGrade = async (student: StudentInfo) => {
    setFetchGradeErrorDismissed(false);
    const { currentScore = null } = await gradingService.fetchGrade({
      student,
    });
    return formatGrade(currentScore, scoreMaximum);
  };

  // The stored grade value fetched from the LMS and converted to the range
  // displayed in the UI.
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

  // This is used to track an unsaved grade. It is null until user input occurs.
  const [draftGradeValue, setDraftGradeValue] = useState<string | null>(null);

  // Track if current grade has changed compared to what was originally loaded
  const hasUnsavedChanges = useMemo(
    () => draftGradeValue !== null && draftGradeValue !== grade.data,
    [draftGradeValue, grade.data]
  );

  // Make sure instructors are notified if there's a risk to lose unsaved data
  useWarnOnPageUnload(hasUnsavedChanges);

  // Clear the previous grade when the user changes.
  useEffect(() => {
    setGradeSaved(false);
    setDraftGradeValue(null);
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current!.focus();
    inputRef.current!.select();
  }, [grade]);

  const onSubmitGrade = async (event: Event) => {
    event.preventDefault();

    const newGrade = inputRef.current!.value;
    const result = validateGrade(newGrade, scoreMaximum);

    if (!result.valid) {
      setValidationMessageMessage(result.error);
      setValidationError(true);
    } else {
      setGradeSaving(true);
      try {
        await gradingService.submitGrade({
          student: student as StudentInfo,
          grade: result.grade,
        });
        grade.mutate(newGrade);
        onUnsavedChanges?.(false);
        setGradeSaved(true);
      } catch (e) {
        setSubmitGradeError(e);
      }
      setGradeSaving(false);
    }
  };

  const handleInput = useCallback(
    (e: Event) => {
      // If any input is detected, close the ValidationMessage.
      setValidationError(false);
      setGradeSaved(false);

      const newDraftGradeValue = (e.target as HTMLInputElement).value;
      setDraftGradeValue(newDraftGradeValue);

      // Check if there are unsavedChanges
      onUnsavedChanges?.(newDraftGradeValue !== grade.data);
    },
    [grade.data, onUnsavedChanges]
  );

  const disabled = !student;

  return (
    <>
      <form autoComplete="off">
        <label htmlFor={gradeId} className="font-semibold text-xs">
          Grade (Out of {scoreMaximum})
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
              onInput={handleInput}
              type="text"
              value={draftGradeValue ?? grade.data ?? ''}
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
