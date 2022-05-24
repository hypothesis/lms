import {
  Icon,
  IconButton,
  LabeledButton,
  Modal,
  Thumbnail,
  TextInputWithButton,
  TextInput,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useRef, useState } from 'preact/hooks';

import { formatErrorMessage } from '../errors';
import { urlPath, useAPIFetch } from '../utils/api';
import { articleIdFromURL, jstorURLFromArticleId } from '../utils/jstor';

/**
 * @template T
 * @typedef {import('../utils/fetch').FetchResult<T>} FetchResult
 */

/**
 * Response for an `/api/jstor/articles/{article_id}` call.
 *
 * @typedef Metadata
 * @prop {string} title
 */

/**
 * Response for an `/api/jstor/articles/{article_id}/thumbnail` call.
 *
 * @typedef Thumbnail
 * @prop {string} image
 */

/**
 * @typedef JSTORPickerProps
 * @prop {() => void} onCancel
 * @prop {(url: string) => void} onSelectURL - Callback to set the assignment's
 *   content to a JSTOR article URL
 */

/**
 * A picker that allows a user to enter a URL corresponding to a JSTOR article.
 *
 * @param {JSTORPickerProps} props
 */
export default function JSTORPicker({ onCancel, onSelectURL }) {
  const [error, setError] = useState(/** @type {string|null} */ (null));

  // Selected JSTOR article ID or DOI, updated when the user confirms what
  // they have pasted/typed into the input field.
  const [articleId, setArticleId] = useState(/** @type {string|null} */ (null));

  /** @type {FetchResult<Metadata>} */
  const metadata = useAPIFetch(
    articleId ? urlPath`/api/jstor/articles/${articleId}` : null
  );

  /** @type {FetchResult<Thumbnail>} */
  const thumbnail = useAPIFetch(
    articleId ? urlPath`/api/jstor/articles/${articleId}/thumbnail` : null
  );

  let renderedError;
  if (error) {
    renderedError = error;
  } else if (metadata.error) {
    renderedError = formatErrorMessage(
      metadata.error,
      'Unable to fetch article details'
    );
  }

  const inputRef = /** @type {{ current: HTMLInputElement }} */ (useRef());
  // The last confirmed value of the URL-entry text input
  const previousURL = useRef(/** @type {string|null} */ (null));

  const canConfirmSelection = articleId && metadata.data !== null;
  const confirmSelection = () => {
    if (canConfirmSelection) {
      onSelectURL(jstorURLFromArticleId(articleId));
    }
  };

  /**
   * @param {boolean} [confirmSelectedUrl=false]
   */
  const onURLChange = (confirmSelectedUrl = false) => {
    const url = inputRef?.current?.value;
    if (url && url === previousURL.current) {
      if (confirmSelectedUrl) {
        confirmSelection();
      }
      return;
    }

    previousURL.current = url;
    setArticleId(null);

    if (!url) {
      // If the field is empty, there's nothing to do
      return;
    }

    const articleId = articleIdFromURL(url);
    if (!articleId) {
      setError("That doesn't look like a JSTOR article link");
      return;
    }

    setError(null);
    setArticleId(articleId);
  };

  /**
   * Capture "Enter" keystrokes, and avoid submitting the entire parent `<form>`
   *
   * @param {KeyboardEvent} event
   */
  const onKeyDown = event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      onURLChange(true /* confirmSelection */);
    }
  };

  const isLoading = thumbnail.isLoading || metadata.isLoading;

  return (
    <Modal
      initialFocus={inputRef}
      onCancel={onCancel}
      contentClass={classnames('LMS-Dialog LMS-Dialog--wide')}
      title="Select JSTOR article"
      buttons={[
        <LabeledButton
          data-testid="select-button"
          disabled={!canConfirmSelection}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Submit
        </LabeledButton>,
      ]}
    >
      <div className="flex flex-row space-x-3">
        <Thumbnail classes="w-32 h-40" isLoading={isLoading}>
          {thumbnail.data && (
            <img alt="article thumbnail" src={thumbnail.data.image} />
          )}
        </Thumbnail>
        <div className="space-y-2 grow">
          <p>Paste a link to the JSTOR article you&apos;d like to use:</p>

          <TextInputWithButton>
            <TextInput
              inputRef={inputRef}
              name="jstorURL"
              onChange={() => onURLChange()}
              onInput={() => setArticleId(null)}
              onKeyDown={onKeyDown}
              placeholder="e.g. https://www.jstor.org/stable/1234"
            />
            <IconButton
              icon="arrowRight"
              onClick={() => onURLChange()}
              variant="dark"
              title="Find article"
            />
          </TextInputWithButton>

          {metadata.data && (
            <div
              className="flex flex-row items-center space-x-2"
              data-testid="selected-book"
            >
              <Icon name="check" classes="text-green-success" />
              <div className="grow font-bold italic">{metadata.data.title}</div>
            </div>
          )}

          {renderedError && (
            <div
              className="flex flex-row items-center space-x-2 text-red-error"
              data-testid="error-message"
            >
              <Icon name="cancel" />
              <div className="grow">{renderedError}</div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
