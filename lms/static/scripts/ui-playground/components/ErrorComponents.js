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

        <ul>
          <li>
            <b>Modes</b>. The front-end application operates in one of{' '}
            <b>four {'"modes"'}</b>.
            <ul>
              <li>
                The current mode is indictated by the JS configuration object
                provided by the back-end.
              </li>
              <li>
                The front-end renders a corresponding top-level application
                component based on the active mode.
              </li>
              <li>
                The four modes and their corresponding app components are:
                <ul>
                  <li>
                    <code>error-dialog</code>: <code>ErrorDialogApp</code>
                  </li>
                  <li>
                    <code>oauth2-redirect-error</code>:{' '}
                    <code>OAuth2RedirectErrorApp</code>
                  </li>
                  <li>
                    <code>basic-lti-launch</code>:{' '}
                    <code>BasicLTILaunchApp</code>
                  </li>
                  <li>
                    <code>content-item-selection</code>:{' '}
                    <code>FilePickerApp</code>
                  </li>
                </ul>
              </li>
            </ul>
          </li>
          <li>
            Different <b>sources of information about errors</b> shown to users.
            These sources include:
            <ul>
              <li>The JS configuration object written by the back-end</li>
              <li>Response bodies from our proxy API</li>
              <li>
                Prepared text to help the user address the specific problem.
                This text is contained in front-end app components, but
                corresponds to an error code provided by the back-end, either in
                the configuration object or in an API response.
              </li>
            </ul>
          </li>
        </ul>
      </div>

      <Library.Pattern title="ErrorDisplay">
        <Library.Example>
          <p>
            The <code>ErrorDisplay</code> component is used to show information
            about errors to users. It is intended to be used within a Modal
            context, and provides a <code>Scrollbox</code> to scroll content if
            it is too tall for the containing element.
          </p>
          <p>
            When information about an error is displayed to a user via{' '}
            <code>ErrorDisplay</code>, we show, in order of render:
          </p>
          <ul>
            <li>
              <p>
                An optional{' '}
                <b>
                  <code>description</code>
                </b>
                . This comes from the front-end app and is treated as a prefix
                to any available error message.
              </p>
            </li>
            <li>
              <p>
                An <b>error message</b>. The message is based on the provided{' '}
                <code>error</code> prop object. If the <code>error</code> has a{' '}
                <code>serverMessage</code> property, that will be used (even if
                empty), otherwise anything present in <code>error.message</code>{' '}
                is rendered.
              </p>

              <p>
                When both a description and a message are shown, they are shown
                separated by a colon, e.g.:
              </p>
              <pre>
                <code>description: message</code>
              </pre>
            </li>
            <li>
              <p>
                Any available <b>prepared/canned text</b> based on{' '}
                <b>error code</b>. This is optionally provided by the front-end
                app as <code>children</code> to the component.
              </p>
            </li>

            <li>
              <p>
                Static <b>how to get more help text</b> that applies in all
                cases. This is always rendered.
              </p>
            </li>
            <li>
              <p>
                Additional <b>error details</b> from by our API responses, based
                on <code>error.details</code>.
              </p>
            </li>
          </ul>
          <Library.Demo withSource title="With description and error message">
            <ErrorDisplay
              error={fakeError}
              description="This is an app-provided description"
            >
              This is an example of prepared/canned text that can be rendered
              depending on the error code at play.
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo
            withSource
            title="With error message but no description"
          >
            <ErrorDisplay error={fakeError}>
              <p>
                This is an example of prepared/canned text that can be rendered
                depending on the error code at play.
              </p>
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo withSource title="Without description or error message">
            <ErrorDisplay error={{ details: { foo: 'bar' } }}>
              <p>
                This is an example of prepared/canned text that can be rendered
                depending on the error code at play.
              </p>
            </ErrorDisplay>
          </Library.Demo>

          <Library.Demo
            withSource
            title="Without description or canned error text"
          >
            <ErrorDisplay error={fakeError} />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
      <Library.Pattern title="ErrorDialog">
        <Library.Example>
          <p>
            <code>ErrorDialog</code> uses the shared <code>Modal</code>{' '}
            component to render information about an {'error-like'} object in
            various places in the front-end app. It wraps an{' '}
            <code>ErrorDisplay</code>.
          </p>
          <Library.Demo>
            <ErrorDialogExample />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
      <Library.Pattern title="ErrorDialogApp">
        <div className="LMSLibrary__content">
          <p>
            These error dialogs are shown when the JS configuration object puts
            the app in <code>error-dialog</code> mode. They indicate that the
            application cannot launch at all.
          </p>
          <p>
            <b>
              Note: The dialogs generated in these examples are non-dismissable.{' '}
            </b>
            You will need to reload this page to {'"dismiss"'} the error dialog,
            even the dialogs with close buttons.
          </p>
        </div>
        <Library.Example title="Recognized error codes">
          <Library.Demo title="Reused consumer key">
            <ErrorDialogAppExample />
          </Library.Demo>
        </Library.Example>

        <Library.Example title="Unrecognized or missing error codes">
          <p>
            This error is shown if the configuration-provided error code is
            unrecognized, or if it is missing.
          </p>
          <Library.Demo title="Generic error">
            <ErrorDialogAppExample errorCode={'some-other'} />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>

      <Library.Pattern title="Oauth2RedirectErrorApp">
        <div className="LMSLibrary__content">
          <p>
            These error dialogs are shown when the JS configuration object puts
            the app in <code>oauth2-redirect-error</code> mode. They indicate
            that the application cannot launch at all without sorting out
            authorization.
          </p>
          <p>
            <b>
              Note: The dialogs generated in these examples are non-dismissable.{' '}
            </b>
            You will need to reload this page to {'"dismiss"'} the error dialog,
            even the dialogs with close buttons.
          </p>
        </div>

        <Library.Example title="Recognized error codes" variant="wide">
          <Library.Demo title="blackboard_missing_integration">
            <OAuth2RedirectErrorAppExample errorCode="blackboard_missing_integration" />
          </Library.Demo>

          <Library.Demo title="canvas_invalid_scope">
            <OAuth2RedirectErrorAppExample errorCode="canvas_invalid_scope" />
          </Library.Demo>
        </Library.Example>

        <Library.Example title="Unrecognized or missing error codes">
          <p>
            This error is shown if the configuration-provided error code is
            unrecognized, or if it is missing.
          </p>
          <Library.Demo title="Any other error code (generic error)">
            <OAuth2RedirectErrorAppExample errorCode={'some-other'} />
          </Library.Demo>
        </Library.Example>
      </Library.Pattern>
    </Library.Page>
  );
}
