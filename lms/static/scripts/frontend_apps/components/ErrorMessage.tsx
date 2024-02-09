import type { ComponentChildren, JSX } from 'preact';

import UIMessage from './UIMessage';

// Excluding role attribute, as it will always be set as `role="alert"`
export type ErrorMessageProps = Omit<
  JSX.HTMLAttributes<HTMLDivElement>,
  'role'
> & {
  error: ComponentChildren;
  role?: never;
};

export default function ErrorMessage({ error, ...rest }: ErrorMessageProps) {
  return (
    <div {...rest} role="alert">
      {!!error && <UIMessage status="error">{error}</UIMessage>}
    </div>
  );
}
