import { Button } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';

import AuthButton from './AuthButton';
import ErrorModal from './ErrorModal';
import type { ErrorModalProps } from './ErrorModal';

type ComponentProps = {
  /** Initial URL for the authorization popup. See `AuthWindow`. */
  authURL: string;
  /** Auth token between the LMS frontend and backend. See `AuthWindow`. */
  authToken: string;

  /**
   * Set the default Cancel button text. Only relevant if `onCancel` is provided
   * (passed through to `ErrorModal`)
   */
  cancelLabel?: string;
  children?: ComponentChildren;

  /**
   * Callback invoked when the authorization flow completes. This does not
   * guarantee that authorization was successful. Instead the caller should
   * retry whatever operation triggered the authorization prompt and check
   * whether it succeeds.
   */
  onAuthComplete: () => void;
  title?: string;
};

export type AuthorizationModalProps = ErrorModalProps & ComponentProps;

/**
 * Render an Authorization modal.
 */
export default function AuthorizationModal({
  authToken,
  authURL,
  children,
  onAuthComplete,

  // ErrorModal props
  cancelLabel = 'Cancel',
  onCancel,
  title = 'Authorize Hypothesis',

  // Other props to forward on to ErrorModal
  ...restProps
}: AuthorizationModalProps) {
  const buttons = (
    <>
      {onCancel && (
        <Button data-testid="cancel-button" onClick={onCancel}>
          {cancelLabel}
        </Button>
      )}
      <AuthButton
        authURL={authURL}
        authToken={authToken}
        onAuthComplete={onAuthComplete}
      />
    </>
  );

  return (
    <ErrorModal
      buttons={buttons}
      cancelLabel={cancelLabel}
      title={title}
      {...restProps}
    >
      {children}
    </ErrorModal>
  );
}
