import {
  Button,
  CancelIcon,
  CheckIcon,
  IconButton,
  Input,
  Spinner,
  SpinnerOverlay,
  NoteIcon,
  NoteFilledIcon,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useEffect,
  useLayoutEffect,
  useState,
  useRef,
  useCallback,
  useMemo,
  useId,
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

  acceptGradingComments?: boolean;
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
  acceptGradingComments = false,
}: SubmitGradeFormProps) {
  const [fetchGradeErrorDismissed, setFetchGradeErrorDismissed] =
    useState(false);
  const gradingService = useService(GradingService);

  const fetchGrade = async (student: StudentInfo) => {
    setFetchGradeErrorDismissed(false);
    const { currentScore = null, comment } = await gradingService.fetchGrade({
      student,
    });
    return {
      grade: formatGrade(currentScore, scoreMaximum),
      comment,
    };
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

  // Comment-related state
  const [showCommentControls, setShowCommentControls] = useState(false);
  const [commentValue, setCommentValue] = useState<string>();
  const commentId = useId();
  // As long as the comment area is not manually edited, we consider a comment
  // is set if one was initially returned.
  // As soon as the area is edited, its value is the source of truth to determine
  // if a comment has been set.
  const commentIsSet =
    commentValue === undefined ? !!grade.data?.comment : !!commentValue;

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
    () => draftGradeValue !== null && draftGradeValue !== grade.data?.grade,
    [draftGradeValue, grade.data]
  );

  // Make sure instructors are notified if there's a risk to lose unsaved data
  useWarnOnPageUnload(hasUnsavedChanges);

  // Clear the previous grade and hide comment controls when the user changes.
  useEffect(() => {
    setGradeSaved(false);
    setShowCommentControls(false);
    setDraftGradeValue(null);
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current!.focus();
    inputRef.current!.select();
  }, [grade]);

  const onSubmitGrade = async (event: Event) => {
    event.preventDefault();

    const newGrade = inputRef.current!.value;
    const newComment = acceptGradingComments ? commentValue : undefined;
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
          comment: newComment,
        });
        grade.mutate({ grade: newGrade, comment: newComment });
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
      onUnsavedChanges?.(newDraftGradeValue !== grade.data?.grade);
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
              value={draftGradeValue ?? grade.data?.grade ?? ''}
              key={student ? student.LISResultSourcedId : null}
            />
            {grade.isLoading && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <Spinner size="md" />
              </div>
            )}
          </span>

          {acceptGradingComments && (
            <span className="relative">
              <Button
                icon={commentIsSet ? NoteFilledIcon : NoteIcon}
                disabled={disabled}
                title={commentIsSet ? 'Edit comment' : 'Add comment'}
                onClick={() => setShowCommentControls(prev => !prev)}
                classes={classnames(
                  'border border-r-0 rounded-none ring-inset h-full',
                  'disabled:opacity-50'
                )}
              />
              <div
                className={classnames(
                  'w-80 p-2 space-y-1',
                  'shadow border bg-white',
                  'absolute top-full right-0',
                  // Hiding via CSS instead of dynamic rendering, so that the
                  // comment is not lost when closed.
                  { hidden: !showCommentControls }
                )}
              >
                <div className="flex items-center">
                  <label htmlFor={commentId} className="font-bold">
                    Add a comment:
                  </label>
                  <div className="grow" />
                  <IconButton
                    title="Close comment"
                    icon={CancelIcon}
                    onClick={() => setShowCommentControls(false)}
                  />
                </div>
                <textarea
                  id={commentId}
                  className={classnames(
                    'focus-visible-ring ring-inset border rounded w-full h-20 p-2',
                    'bg-grey-0 focus:bg-white disabled:bg-grey-1',
                    'placeholder:text-color-grey-5 disabled:placeholder:color-grey-6'
                  )}
                  defaultValue={grade.data?.comment ?? ''}
                  value={commentValue}
                  onChange={e =>
                    setCommentValue((e.target as HTMLTextAreaElement).value)
                  }
                />
              </div>
            </span>
          )}

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
