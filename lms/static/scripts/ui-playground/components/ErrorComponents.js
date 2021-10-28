import { useState } from 'preact/hooks';

import { LabeledButton } from '@hypothesis/frontend-shared';

import { Config } from '../../frontend_apps/config';

import ErrorDialogApp from '../../frontend_apps/components/ErrorDialogApp';
import ErrorDisplay from '../../frontend_apps/components/ErrorDisplay';
import ErrorDialog from '../../frontend_apps/components/ErrorDialog';
import OAuth2RedirectErrorApp from '../../frontend_apps/components/OAuth2RedirectErrorApp';

import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';

const fakeDetails = {
  foo: { bar: 'These fake details...' },
  errorNonsense:
    'Are JSON-stringified from a `details` property on an {ErrorLike} object',
};
const fakeError = {
  message: 'This is an error message',
  details: fakeDetails,
};

function ErrorDialogExample() {
  const [dialogOpen, setDialogOpen] = useState(false);

  if (!dialogOpen) {
    return (
      <LabeledButton
        onClick={() => setDialogOpen(!dialogOpen)}
        variant="primary"
      >
        Show ErrorDialog Example
      </LabeledButton>
    );
  } else {
    return (
      <ErrorDialog
        error={fakeError}
        onCancel={() => setDialogOpen(false)}
        description="Sample Error"
      />
    );
  }
}

function ErrorDialogAppExample({ errorCode = 'reused_consumer_key' }) {
  const config = { api: {}, errorDialog: { errorCode } };
  const [dialogOpen, setDialogOpen] = useState(false);

  if (!dialogOpen) {
    return (
      <LabeledButton
        onClick={() => setDialogOpen(!dialogOpen)}
        variant="primary"
      >
        Show ErrorDialogApp Example
      </LabeledButton>
    );
  } else {
    return (
      <Config.Provider value={config}>
        <ErrorDialogApp />
      </Config.Provider>
    );
  }
}

function OAuth2RedirectErrorAppExample({ errorCode = '' }) {
  const config = {
    api: {},
    OAuth2RedirectError: {
      errorCode,
      canvasScopes: [
        'This is a fake Canvas scope',
        'These scopes would be',
        'Written to the JS configuration object',
        'By the back end in real life',
      ],
      errorDetails: fakeDetails,
    },
  };
  const [dialogOpen, setDialogOpen] = useState(false);

  if (!dialogOpen) {
    return (
      <LabeledButton
        onClick={() => setDialogOpen(!dialogOpen)}
        variant="primary"
      >
        Show OAuth2RedirectErrorApp Example
      </LabeledButton>
    );
  } else {
    return (
      <Config.Provider value={config}>
        <OAuth2RedirectErrorApp />
      </Config.Provider>
    );
  }
}

export default function ErrorComponents() {
  return (
    <Library.Page title="Errors">
      <div className="LMSLibrary__content">
        <h2>Intro</h2>
        <p>To understand errors it is useful to understand:</p>
        <h3>Modes</h3>
        <ul>
          <li>
            The front-end application operates in one of <b>four {'"modes"'}</b>
            .
          </li>
          <li>
            The front-end application determines which{' '}
            <b>top-level application component</b> to render based on mode.
          </li>
          <li>
            The back-end writes a <b>JS configuration object</b> to the page to
            inform the front-end app which mode to operate in.
          </li>
        </ul>

        <h3>Where error information {'"comes from"'}</h3>
        <p>
          When displaying error information to users, the variable parts of the
          error information shown come from multiple sources:
        </p>
        <ul>
          <li>
            When in one of the two error modes, error information (including
            error code) is provided by the backend in the JS configuration
            object.
          </li>
          <li>
            When errors arise from making requests to our own proxy API, error
            messaging, error code, and error details are returned in the
            response body.
          </li>
          <li>
            When the UI components render information about JavaScript errors
            not arising from our API, the JavaScript Error message may be shown.
          </li>
        </ul>

        <h2>Errors that prevent the application from launching usefully</h2>
        <h3>
          <code>error-dialog</code> and <code>oauth-redirect-error</code> modes
        </h3>
        <p>
          In some cases, errors arising from the back-end prevent the front-end
          application from being able to operate usefully.
        </p>
        <p>
          In these situations, the backend writes some information to the
          JavaScript configuration object in the page that indicates that the
          application should be in one of two error {"'modes'"} (
          <code>error-dialog</code> or <code>oauth-redirect-error</code>)
          handled by two top-level app components (<code>ErrorDialogApp</code>{' '}
          and <code>OAuth2RedirectErrorApp</code>). Additional error information
          (e.g. an error code dictating which canned text should be shown to the
          user) is also included in the configuration object.
        </p>
        <p>
          An example of this kind of error is a reused consumer key or missing
          scopes.
        </p>
        <p>
          Errors of this class represent a sort of {'"game over"'} and
          information about them is rendered in a non-dismissable dialog.
        </p>

        <h2>Errors that arise when launching assignments</h2>
        <p>
          Another class of errors involves problems during assignment launch,
          when in the <code>basic-lti-launch</code> mode of the application.
        </p>
        <p>
          These typically arise when fetch requests to our proxy API result in
          an error response.
        </p>
        <p>
          An example of this type of error is if a Canvas file needed for the
          assignment cannot be found or accessed.
        </p>
        <p>
          This type of error is shown in a dialog, usually with a{' '}
          {'"Try again"'} action.
        </p>
        <p>
          Information shown to the user sometimes includes static text
          associated with the error response error code, for example, how to fix
          a missing Canvas file.
        </p>

        <p>TODO</p>

        <h3>Errors that arise when grading assignments</h3>

        <p>
          Assignment grading occurs within the <code>basic-lti-launch</code>{' '}
          mode of the application.
        </p>

        <p>TODO</p>

        <h2>Errors that arise when configuring assignments</h2>
        <p>
          Errors can also arise when configuring assignments, in the{' '}
          {"application's"} <code>content-item-selection</code> mode.
        </p>
        <p>
          These errors arise from our own proxy API, and also from integrations
          with other APIs (e.g. Google Drive).
        </p>
        <p>TODO</p>
      </div>

      <Library.Pattern title="ErrorDisplay">
        <Library.Example>
          <p>
            All of the errors described here, with rare exception, use the{' '}
            <code>ErrorDisplay</code> component to show their core details.
          </p>
          <p>
            It is intended to be used within a Modal context, and provides a{' '}
            <code>Scrollbox</code> to scroll content if it is too tall for the
            containing element.
          </p>
          <p>
            When information about an error is displayed to a user, we show:
          </p>
          <ul>
            <li>
              <p>
                <b>Prepared/canned text</b> based on <b>error code</b>
              </p>
              <p>
                Canned text for different kinds of errors is defined in the
                front-end app, for example, instructions on how to rectify a
                missing Canvas file. Which canned text gets displayed is
                determined by an error code provided by the back end. Depending
                on the error context, this error code may either be in the JS
                configuration object (error {'"modes"'}) or within the response
                body of a problematic request to our proxy API.
              </p>
              <p>
                Canned text is <b>sometimes</b> shown. It depends on whether a
                recognized error code is provided. It is not relevant to all
                error cases.
              </p>
            </li>
            <li>
              <p>
                A brief <b>contextual hint</b>
              </p>
              <p>
                Also called a <b>description</b>, this text is provided in some
                cases by the front-end app to provide context for the error,
                e.g. {'"There was an error fetching book chapters"'}.
              </p>
              <p>
                Contextual hints are <b>sometimes shown</b>.
              </p>
            </li>
            <li>
              <p>
                A brief <b>error message</b>
              </p>
              <p>
                Whereas the contextual hint is provided directly to the{' '}
                <code>ErrorDisplay</code> component by the app, the message is
                based on the error object at play. What, if any, message gets
                displayed follows this logic:
              </p>
              <ul>
                <li>
                  For error responses from our own API: the server-provided
                  message within the response body of the failed request. If no
                  server-provided message is present, no message will be
                  displayed.
                </li>
                <li>
                  For other types of JavaScript Error objects, or error-like
                  objects, the <code>message</code> property of the Error, if
                  present.
                </li>
              </ul>
              <p>
                When both a contextual hint and a message are shown, they are
                shown separated by a colon, e.g.:
              </p>
              <pre>
                <code>description: message</code>
              </pre>
              <p>
                A message is <b>sometimes shown</b>.
              </p>
            </li>
            <li>
              <p>
                Static canned <b>user-help text</b>
              </p>
              <p>
                This provides basic links and help instructions and is{' '}
                <b>always shown</b>.
              </p>
            </li>
            <li>
              <p>
                Additional <b>error details</b> provided by our API
              </p>
              <p>
                For errors from requests to our API, any <code>details</code> in
                the response body will be JSON-stringified and shown in a
                collapsed details section. Details are <b>sometimes shown.</b>
              </p>
            </li>
          </ul>
          <Library.Demo withSource title="With contextual hint and message">
            <ErrorDisplay
              error={fakeError}
              description="This is an app-provided contextual hint"
            >
              This is an example of prepared/canned text that can be rendered
              depending on the error code at play.
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo withSource title="Without contextual hint">
            <ErrorDisplay error={fakeError}>
              <p>
                This is an example of prepared/canned text that can be rendered
                depending on the error code at play.
              </p>
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo withSource title="Without contextual hint or message">
            <ErrorDisplay error={{ details: { foo: 'bar' } }}>
              <p>
                This is an example of prepared/canned text that can be rendered
                depending on the error code at play.
              </p>
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo
            withSource
            title="Without canned/error-code text or contextual hint"
          >
            <ErrorDisplay error={fakeError} />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
      <Library.Pattern title="Error-mode errors">
        <div className="LMSLibrary__content">
          <h3>
            Errors that prevent the application from launching usefully at all
          </h3>
          <p>
            These errors are displayed when the app is in{' '}
            <code>error-dialog</code> mode (<code>ErrorDialogApp</code>{' '}
            component) or <code>oauth2-redirect-error</code> mode (
            <code>OAuth2RedirectErrorApp</code> component).
          </p>
          <p>
            <b>
              Note: The dialogs generated in these examples are non-dismissable.{' '}
            </b>
            You will need to reload this page to {'"dismiss"'} the error dialog,
            even the dialogs with close buttons.
          </p>
        </div>
        <Library.Example title="ErrorDialogApp (recognized error codes)">
          <p>
            These errors are shown when the app is in <code>error-dialog</code>{' '}
            mode (<code>ErrorDialogApp</code> component). The static text shown
            to the user is provided by the front-end app based on the error code
            written to the JS configuration object.
          </p>
          <p>
            At time of writing the only recognized error code is{' '}
            <code>reused_consumer_key</code>.
          </p>
          <Library.Demo title="Reused consumer key">
            <ErrorDialogAppExample />
          </Library.Demo>
        </Library.Example>

        <Library.Example title="ErrorDialogApp (generic/unrecognized or missing error code)">
          <p>
            This error is shown if the configuration-provided error code is
            unrecognized, or if it is missing.
          </p>
          <Library.Demo title="Any other error code (generic error)">
            <ErrorDialogAppExample errorCode={'some-other'} />
          </Library.Demo>
        </Library.Example>

        <Library.Example title="OAuth2RedirectErrorApp (recognized error codes)">
          <p>
            These errors are shown when the app is in{' '}
            <code>oauth2-redirect-error</code> mode (
            <code>OAuth2RedirectErrorApp</code> component). The static text
            shown to the user is provided by the front-end app based on the
            error code written to the JS configuration object.
          </p>
          <p>
            At time of writing the recognized error codes are{' '}
            <code>blackboard_missing_integration</code> and{' '}
            <code>canvas_invalid_scope</code>.
          </p>
          <Library.Demo title="blackboard_missing_integration">
            <OAuth2RedirectErrorAppExample errorCode="blackboard_missing_integration" />
          </Library.Demo>

          <Library.Demo title="canvas_invalid_scope">
            <OAuth2RedirectErrorAppExample errorCode="canvas_invalid_scope" />
          </Library.Demo>
        </Library.Example>

        <Library.Example title="OAuth2RedirectErrorApp (generic/unrecognized or missing error code)">
          <p>
            This error is shown if the configuration-provided error code is
            unrecognized, or if it is missing.
          </p>
          <Library.Demo title="Any other error code (generic error)">
            <OAuth2RedirectErrorAppExample errorCode={'some-other'} />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
      <Library.Pattern title="ErrorDialog">
        <Library.Example>
          <p>
            <code>ErrorDialog</code> uses the shared <code>Modal</code>{' '}
            component to render information about an {'error-like'} object.
            <ul>
              <li>The Modal title is always {'"Something went wrong"'}</li>
              <li>
                The <code>description</code> (optional) and <code>error</code>{' '}
                props are forwarded to <code>ErrorDisplay</code>, which is
                rendered as the body of the Modal.
              </li>
              <li>
                The label on the cancel/close button may be set with the{' '}
                <code>cancelLabel</code> prop
              </li>
            </ul>
          </p>
          <Library.Demo>
            <ErrorDialogExample />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
    </Library.Page>
  );
}
