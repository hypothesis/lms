import type { ComponentChildren, JSX } from 'preact';

import UIMessage from './UIMessage';

// Excluding aria-live, as it will always be set as `aria-live="polite"
export type ErrorMessageProps = Omit<
  JSX.HTMLAttributes<HTMLDivElement>,
  'aria-live'
> & {
  error: ComponentChildren;
  'aria-live'?: never;
};

/**
 * Renders a UIMessage[status="error"], with [role="alert"] and wrapped in an
 * always-present [aria-live="polite"] container
 */
export default function ErrorMessage({ error, ...rest }: ErrorMessageProps) {
  return (
    <div {...rest} aria-live="polite">
      {!!error && (
        <UIMessage status="error" role="alert">
          {error}
        </UIMessage>
      )}
    </div>
  );
}
