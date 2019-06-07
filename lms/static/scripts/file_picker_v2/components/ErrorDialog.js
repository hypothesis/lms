import { createElement } from 'preact';
import propTypes from 'prop-types';

import Dialog from './Dialog';

/**
 * Informs the user that a problem occurred and provides them with useful links
 * to get help or report the issue.
 */
export default function ErrorDialog({ title, error }) {
  return (
    <Dialog title="Something went wrong :(">
      <p>{title}</p>
      <p>
        If you have a problem using Hypothesis LMS integration, please{' '}
        <a
          href="https://web.hypothes.is/help/"
          target="_blank"
          rel="noopener noreferrer"
        >
          visit our support page
        </a>
        .
      </p>
      <p>Problem details: {error.message}</p>
    </Dialog>
  );
}

ErrorDialog.propTypes = {
  title: propTypes.string.isRequired,
  error: propTypes.shape({
    message: propTypes.string.isRequired,
  }),
};
