import { Link } from '@hypothesis/frontend-shared';

import { useConfig } from '../config';
import ErrorModal from './ErrorModal';

export type OAuth2RedirectErrorAppProps = {
  /* Test seam */
  location?: Location;
};

/**
 * Error Modal displayed when authorization with a third-party API via OAuth
 * fails.
 *
 * Dismissing the Modal will close the window.
 */
export default function OAuth2RedirectErrorApp({
  location = window.location,
}: OAuth2RedirectErrorAppProps) {
  const {
    OAuth2RedirectError: {
      authUrl = null,
      errorCode,
      errorDetails = '',
      canvasScopes = [],
    },
  } = useConfig(['OAuth2RedirectError']);

  const error = { errorCode, details: errorDetails };

  let title;
  let description;
  switch (errorCode) {
    case 'canvas_invalid_scope':
      title = 'Developer key scopes missing';
      break;
    case 'blackboard_missing_integration':
      title = 'Missing Blackboard REST API integration';
      break;
    default:
      title = 'Authorization failed';
      description = 'Something went wrong when authorizing Hypothesis';
      break;
  }

  const retry = () => {
    location.href = authUrl!;
  };
  const onRetry = authUrl ? retry : undefined;

  return (
    <ErrorModal
      cancelLabel="Close"
      description={description}
      error={error}
      onCancel={() => window.close()}
      onRetry={onRetry}
      title={title}
      size="lg"
    >
      {errorCode === 'canvas_invalid_scope' && (
        <>
          <p>
            A Canvas admin needs to edit {"Hypothesis's"} developer key and add
            these scopes:
          </p>
          <ol className="pl-8 list-decimal">
            {canvasScopes.map(scope => (
              <li key={scope}>
                <code>{scope}</code>
              </li>
            ))}
          </ol>
          <p>
            For more information see:{' '}
            <Link
              target="_blank"
              href="https://github.com/hypothesis/lms/wiki/Canvas-API-Endpoints-Used-by-the-Hypothesis-LMS-App"
              underline="always"
            >
              Canvas API Endpoints Used by the Hypothesis LMS App
            </Link>
            .
          </p>
        </>
      )}

      {errorCode === 'blackboard_missing_integration' && (
        <>
          <p>
            In order to allow Hypothesis to connect to files in Blackboard, your
            Blackboard admin needs to add or enable a REST API integration.
          </p>
          <p>
            For more information, please have your Blackboard admin read:{' '}
            <Link
              classes="inline"
              target="_blank"
              href="https://web.hypothes.is/help/enable-the-hypothesis-integration-with-blackboard-files/"
              underline="always"
            >
              Enable the Hypothesis Integration With Blackboard Files
            </Link>
            .
          </p>
        </>
      )}
    </ErrorModal>
  );
}
