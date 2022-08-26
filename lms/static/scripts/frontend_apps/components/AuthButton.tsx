import { LabeledButton } from '@hypothesis/frontend-shared';
import { useCallback, useEffect, useRef } from 'preact/hooks';

import AuthWindow from '../utils/AuthWindow';

type AuthButtonProps = {
  /** Initial URL for the authorization popup. See {@link AuthWindow}. */
  authURL: string;
  /** Auth token between the LMS frontend and backend. See {@link AuthWindow}. */
  authToken: string;

  /** Custom label for the "Authorize" button. */
  label?: string;

  /**
   * Callback invoked when the authorization flow completes.
   *
   * This does not guarantee that authorization was successful. Instead the
   * caller should retry whatever operation triggered the authorization prompt
   * and check whether it succeeds.
   */
  onAuthComplete: () => void;
};

/**
 * Button that prompts the user to authorize the Hypothesis LMS app to access
 * their data in the LMS (or another service).
 *
 * This component is typically shown to the user when an attempt to fetch data
 * from the LMS via an LMS-specific API fails, requiring the user to complete
 * an OAuth or OAuth-like authentication flow before the attempt can proceed.
 */
export default function AuthButton({
  authURL,
  authToken,
  label = 'Authorize',
  onAuthComplete,
}: AuthButtonProps) {
  const authWindow = useRef<AuthWindow | null>(null);

  const authorize = useCallback(async () => {
    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }

    authWindow.current = new AuthWindow({ authToken, authUrl: authURL });

    try {
      await authWindow.current.authorize();
      onAuthComplete();
    } finally {
      authWindow.current.close();
      authWindow.current = null;
    }
  }, [authToken, authURL, onAuthComplete]);

  // Close auth window if component is unmounted.
  useEffect(() => {
    return () => {
      authWindow.current?.close();
    };
  }, []);

  return (
    <LabeledButton onClick={authorize} variant="primary">
      {label}
    </LabeledButton>
  );
}
