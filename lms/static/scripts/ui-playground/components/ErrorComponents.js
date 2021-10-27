import { useState } from 'preact/hooks';

import { LabeledButton } from '@hypothesis/frontend-shared';

import ErrorDisplay from '../../frontend_apps/components/ErrorDisplay';
import ErrorDialog from '../../frontend_apps/components/ErrorDialog';

// TODO: Update after https://github.com/hypothesis/frontend-shared/issues/179
// is resolved
import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';

const fakeError = {
  message:
    'This is a the value of a `message` property on an {ErrorLike} object',
  details: {
    foo: { bar: 'These fake details...' },
    errorNonsense:
      'Are JSON-stringified from a `details` property on an {ErrorLike} object',
  },
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

export default function ErrorComponents() {
  return (
    <Library.Page title="Errors">
      <Library.Pattern title="ErrorDisplay">
        <Library.Example>
          <p>
            The <code>ErrorDisplay</code> component renders information about an
            error. It is the entire body/contents of the{' '}
            <code>ErrorDialog</code> component. It is also used by several other
            components (<code>BookPicker</code>, <code>LaunchErrorDialog</code>,{' '}
            <code>LMSFilePicker</code>, <code>OAuth2RedirectErrorApp</code>...)
          </p>
          <p>
            It is intended to be used within a Modal context, and provides a{' '}
            <code>Scrollbox</code> to scroll content if it is too tall for the
            containing element.
          </p>
          <p>The instructive text is hard-coded at present.</p>
          <Library.Demo withSource>
            <ErrorDisplay
              error={fakeError}
              description="This is a hard-coded description provided in the 'description' prop"
            />
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
