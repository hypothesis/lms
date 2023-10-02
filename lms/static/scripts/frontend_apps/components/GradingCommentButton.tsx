import type { ButtonProps, TextareaProps } from '@hypothesis/frontend-shared';
import {
  Button,
  CancelIcon,
  CloseButton,
  Dialog,
  NoteFilledIcon,
  NoteIcon,
  PointerUpIcon,
  Textarea,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useId, useRef, useState } from 'preact/hooks';

type CommentPopoverProps = {
  comment: string;
  onInput: NonNullable<TextareaProps['onInput']>;
  onSubmit: NonNullable<ButtonProps['onClick']>;
  closePopover: () => void;
};

function CommentPopover({
  comment,
  onInput,
  onSubmit,
  closePopover,
}: CommentPopoverProps) {
  const commentRef = useRef<HTMLTextAreaElement | null>(null);
  const commentId = useId();

  return (
    <Dialog
      variant="custom"
      classes={classnames(
        'w-80 p-3',
        'shadow border rounded bg-white',
        'absolute top-[calc(100%+3px)] right-0'
      )}
      data-testid="comment-popover"
      onClose={closePopover}
      initialFocus={commentRef}
      restoreFocus
      closeOnClickAway
      closeOnEscape
    >
      <PointerUpIcon
        className={classnames(
          'text-grey-3 fill-white',
          'absolute inline z-2 w-[15px]',
          // Position arrow over "Add comment" button
          'right-[7px] top-[-9px]'
        )}
      />
      <div className="flex items-center">
        <label htmlFor={commentId} className="font-bold">
          Add a comment:
        </label>
        <div className="grow" />
        <CloseButton
          title="Close comment"
          classes="hover:bg-grey-3/50"
          data-testid="comment-textless-close-button"
        />
      </div>
      <Textarea
        id={commentId}
        classes="mt-1"
        rows={10}
        value={comment}
        onInput={onInput}
        elementRef={commentRef}
      />
      <div className="flex flex-row-reverse space-x-2 space-x-reverse mt-3">
        <Button
          variant="primary"
          onClick={e => {
            onSubmit(e);
            closePopover();
          }}
          data-testid="comment-submit-button"
        >
          Submit Grade
        </Button>
        <Button
          icon={CancelIcon}
          onClick={closePopover}
          data-testid="comment-close-button"
        >
          Close
        </Button>
      </div>
    </Dialog>
  );
}

export type GradingCommentProps = {
  disabled: boolean;
  loading: boolean;
  comment: string;
  onInput: NonNullable<TextareaProps['onInput']>;
  onSubmit: NonNullable<ButtonProps['onClick']>;
};

/**
 * Grading comment toggle button and popover.
 */
export default function GradingCommentButton({
  disabled,
  loading,
  comment,
  onInput,
  onSubmit,
}: GradingCommentProps) {
  const [showCommentPopover, setShowCommentPopover] = useState(false);
  const closeCommentPopover = useCallback(
    () => setShowCommentPopover(false),
    []
  );
  const commentIsSet = !loading && !!comment;

  return (
    <span className="relative">
      <Button
        icon={commentIsSet ? NoteFilledIcon : NoteIcon}
        disabled={disabled}
        title={commentIsSet ? 'Edit comment' : 'Add comment'}
        onClick={() => setShowCommentPopover(prev => !prev)}
        expanded={showCommentPopover}
        classes={classnames(
          'border border-r-0 rounded-none ring-inset h-full relative',
          'disabled:opacity-50'
        )}
        data-testid="comment-toggle-button"
      />
      {showCommentPopover && (
        <CommentPopover
          closePopover={closeCommentPopover}
          comment={comment}
          onInput={onInput}
          onSubmit={onSubmit}
        />
      )}
    </span>
  );
}
