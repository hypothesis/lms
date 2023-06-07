import { CancelIcon, CheckIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren, JSX } from 'preact';

export type UIMessageProps = {
  status?: 'success' | 'error' | 'info';
  children: ComponentChildren;
} & JSX.HTMLAttributes<HTMLDivElement>;

/**
 * Style a UI message associated with content-picking user inputs
 */
export default function UIMessage({
  status = 'info',
  children,
  ...htmlAttributes
}: UIMessageProps) {
  let Icon;
  if (status === 'error') {
    Icon = CancelIcon;
  } else if (status === 'success') {
    Icon = CheckIcon;
  }
  return (
    <div
      data-component="UIMessage"
      className={classnames('flex gap-x-1', {
        'text-red-error': status === 'error',
      })}
      {...htmlAttributes}
    >
      {Icon && (
        <div>
          <Icon
            className={classnames('w-4 h-4', {
              'text-red-error': status === 'error',
              'text-green-success': status === 'success',
            })}
            data-testid="uimessage-icon"
          />
        </div>
      )}
      <div className="grow">{children}</div>
    </div>
  );
}
