import type { TextareaProps } from '@hypothesis/frontend-shared';
import {
  Button,
  CancelIcon,
  IconButton,
  NoteFilledIcon,
  NoteIcon,
  PointerUpIcon,
  Textarea,
  useClickAway,
  useKeyPress,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useCallback,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from 'preact/hooks';

type CommentPopoverProps = {
  disabled: boolean;
  comment: string;
  onInput?: TextareaProps['onInput'];
  onSubmit?: (e: Event) => Promise<boolean>;
  closePopover: () => void;
};

function CommentPopover({
  disabled,
  comment,
  onInput,
  onSubmit,
  closePopover,
}: CommentPopoverProps) {
  const commentRef = useRef<HTMLTextAreaElement | null>(null);
  const commentId = useId();

  // Focus comment textarea when popover is open
  useLayoutEffect(() => {
    commentRef.current!.focus();
  }, []);

  return (
    <div
      role="dialog"
      className={classnames(
        'w-80 p-3',
        'shadow border rounded bg-white',
        'absolute top-[calc(100%+3px)] right-0'
      )}
      data-testid="comment-popover"
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
        <IconButton
          title="Close comment"
          icon={CancelIcon}
          classes="hover:bg-grey-3/50"
          onClick={closePopover}
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
          disabled={disabled}
          onClick={async e => {
            if (await onSubmit?.(e)) {
              closePopover();
            }
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
    </div>
  );
}

export type GradingCommentProps = Omit<CommentPopoverProps, 'closePopover'>;

export default function GradingComment({
  disabled,
  comment,
  onInput,
  onSubmit,
}: GradingCommentProps) {
  const [showCommentPopover, setShowCommentPopover] = useState(false);
  const closeCommentPopover = useCallback(
    () => setShowCommentPopover(false),
    []
  );
  const commentIsSet = !disabled && !!comment;
  const containerRef = useRef<HTMLSpanElement | null>(null);

  useKeyPress(['Escape'], closeCommentPopover);
  useClickAway(containerRef, closeCommentPopover);

  return (
    <span className="relative" ref={containerRef}>
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
          disabled={disabled}
          closePopover={closeCommentPopover}
          comment={comment}
          onInput={onInput}
          onSubmit={onSubmit}
        />
      )}
    </span>
  );
}
