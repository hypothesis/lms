import {
  Button,
  CheckIcon,
  Input,
  Spinner,
  SpinnerOverlay,
  useWarnOnPageUnload,
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
import { formatGrade } from '../utils/grade-validation';
import { useUniqueId } from '../utils/hooks';
import ErrorModal from './ErrorModal';
import GradingCommentButton from './GradingCommentButton';

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

  /**
   * Allow instructors to provide an extra comment together with the grade value.
   * Default value is false.
   */
  acceptComments?: boolean;
};

const DEFAULT_MAX_SCORE = 10;

type DraftGrading = {
  grade: string | null;
  comment: string | null;
};

/** Return true if there are unsaved changes to the grade. */
function hasGradeChanged(
  draft: DraftGrading,
  savedGrade?: { grade: string; comment: string | null | undefined } | null,
): boolean {
  return (
    (draft.grade !== null && draft.grade !== savedGrade?.grade) ||
    (draft.comment !== null && draft.comment !== savedGrade?.comment)
  );
}

/**
 * A form with a single input field and submit button for an instructor to
 * save a student's grade.
 */
export default function SubmitGradeForm({
  student,
  onUnsavedChanges,
  scoreMaximum = DEFAULT_MAX_SCORE,
  acceptComments = false,
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
    student ? () => fetchGrade(student) : undefined,
  );

  // The following is state for saving the grade
  //
  // If there is an error when submitting a grade?
  const [submitGradeError, setSubmitGradeError] = useState<ErrorLike | null>(
    null,
  );
  // Is set to true when the grade is being currently posted to the service
  const [gradeSaving, setGradeSaving] = useState(false);
  // Changes the input field's background to green for a short duration when true
  const [gradeSaved, setGradeSaved] = useState(false);

  const disabled = !student;

  // Unique id attribute for <input>
  const gradeId = useUniqueId('SubmitGradeForm__grade:');

  // Used to handle keyboard input changes for the grade input field.
  const inputRef = useRef<HTMLInputElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  // This is used to track unsaved grades or comments. It is null until user input occurs.
  const [draftGrading, setDraftGrading] = useState<DraftGrading>({
    grade: null,
    comment: null,
  });
  const updateDraftGrading = useCallback(
    (update: Partial<DraftGrading>) => {
      const newDraftGrading = {
        grade: update.grade ?? draftGrading.grade,
        comment: update.comment ?? draftGrading.comment,
      };

      onUnsavedChanges?.(hasGradeChanged(newDraftGrading, grade.data));
      setDraftGrading(prev => ({ ...prev, ...update }));
    },
    [draftGrading.grade, draftGrading.comment, onUnsavedChanges, grade.data],
  );

  // Track if current grade has changed compared to what was originally loaded
  const hasUnsavedChanges = useMemo(
    () => hasGradeChanged(draftGrading, grade.data),
    [draftGrading, grade.data],
  );

  // Make sure instructors are notified if there's a risk to lose unsaved data
  useWarnOnPageUnload(hasUnsavedChanges);

  // Clear the previous grade when the user changes.
  useEffect(() => {
    setGradeSaved(false);
    setDraftGrading({ grade: null, comment: null });
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current!.focus();
    inputRef.current!.select();
  }, [grade]);

  const onSubmitGrade = async (event: Event) => {
    event.preventDefault();

    const newGrade = inputRef.current!.value;
    const newGradeAsNumber = inputRef.current!.valueAsNumber;
    if (isNaN(newGradeAsNumber)) {
      // This branch should not be reached because input type is number, and we validate before submission.
      throw new Error(`New grade "${newGrade}" is not a number`);
    }

    const newComment = acceptComments
      ? (draftGrading.comment ?? grade.data?.comment)
      : undefined;

    setGradeSaving(true);
    try {
      await gradingService.submitGrade({
        student: student as StudentInfo,
        grade: newGradeAsNumber / scoreMaximum,
        comment: newComment ?? undefined,
      });
      grade.mutate({ grade: newGrade, comment: newComment });
      onUnsavedChanges?.(false);
      setGradeSaved(true);
    } catch (e) {
      setSubmitGradeError(e);
    }
    setGradeSaving(false);
  };

  const submitGrade = useCallback(() => {
    const form = formRef.current;

    // Checks if the form is valid, and display native validation popups if needed
    if (!form || !form.reportValidity()) {
      return false;
    }

    form.requestSubmit();
    return true;
  }, []);

  const handleInput = useCallback(
    (e: Event, field: keyof DraftGrading) => {
      setGradeSaved(false);

      const newValue = (e.target as HTMLInputElement).value;
      updateDraftGrading({ [field]: newValue });
    },
    [updateDraftGrading],
  );

  return (
    <>
      <form autoComplete="off" onSubmit={onSubmitGrade} ref={formRef}>
        <label htmlFor={gradeId} className="font-semibold text-xs">
          Grade (Out of {scoreMaximum})
        </label>
        <div className="flex">
          <span className="relative w-14">
            <Input
              classes={classnames(
                // Hide up/down arrow buttons (https://stackoverflow.com/a/75872055)
                '[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none',
                'text-center',
                'disabled:opacity-50',
                'border border-r-0 rounded-r-none',
                {
                  'animate-gradeSubmitSuccess': gradeSaved,
                },
              )}
              data-testid="grade-input"
              disabled={disabled}
              id={gradeId}
              elementRef={inputRef}
              onInput={e => handleInput(e, 'grade')}
              type="number"
              value={draftGrading.grade ?? grade.data?.grade ?? ''}
              key={student ? student.LISResultSourcedId : null}
              min={0}
              max={scoreMaximum}
              step="any"
              required
            />
            {grade.isLoading && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <Spinner size="md" />
              </div>
            )}
          </span>

          {acceptComments && (
            <GradingCommentButton
              disabled={disabled}
              loading={grade.isLoading}
              comment={draftGrading.comment ?? grade.data?.comment ?? ''}
              onInput={e => handleInput(e, 'comment')}
              onSubmit={submitGrade}
            />
          )}

          <Button
            icon={CheckIcon}
            type="submit"
            data-testid="submit-button"
            classes={classnames(
              'border rounded-l-none ring-inset',
              'disabled:opacity-50',
            )}
            disabled={disabled}
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
