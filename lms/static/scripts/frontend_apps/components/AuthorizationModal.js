import AuthButton from './AuthButton';
import ErrorModal from './ErrorModal';

/**
 * @typedef {import('./ErrorModal').ErrorModalProps} ErrorModalProps
 * @typedef {import("preact").ComponentChildren} Children
 */

/**
 * @typedef AuthorizationModalBaseProps
 * @prop {string} authURL - Initial URL for the authorization popup. See `AuthWindow`.
 * @prop {string} authToken - Auth token between the LMS frontend and backend. See `AuthWindow`.
 * @prop {string} [cancelLabel="Cancel"] - Set the default Cancel button text. Only relevant
 *   if `onCancel` is provided (passed through to `ErrorModal`)
 * @prop {Children} [children]
 * @prop {() => void} onAuthComplete - Callback invoked when the authorization flow completes.
 *   This does not guarantee that authorization was successful. Instead
 *   the caller should retry whatever operation triggered the authorization
 *   prompt and check whether it succeeds.
 * @prop {string} [title="Authorize Hypothesis"]
 *
 */

/**
 * @typedef {Omit<ErrorModalProps, "cancelLabel"|"children"|"title"> & AuthorizationModalBaseProps} AuthorizationModalProps
 * */

/**
 * Render an Authorization modal.
 *
 * @param {AuthorizationModalProps} props
 */
export default function AuthorizationModal({
  authToken,
  authURL,
  cancelLabel = 'Cancel',
  children,
  onAuthComplete,
  title = 'Authorize Hypothesis',

  // Other props to forward on to ErrorModal
  ...restProps
}) {
  const buttons = (
    <AuthButton
      authURL={authURL}
      authToken={authToken}
      onAuthComplete={onAuthComplete}
    />
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
