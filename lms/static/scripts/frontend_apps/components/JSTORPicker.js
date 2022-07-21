import {
  Icon,
  IconButton,
  LabeledButton,
  Link,
  Modal,
  Thumbnail,
  TextInputWithButton,
  TextInput,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useRef, useState } from 'preact/hooks';

import { formatErrorMessage } from '../errors';
import { urlPath, useAPIFetch } from '../utils/api';
import { articleIdFromUserInput, jstorURLFromArticleId } from '../utils/jstor';

/**
 * @typedef {import('../api-types').JSTORMetadata} JSTORMetadata
 * @typedef {import('../api-types').JSTORThumbnail} JSTORThumbnail
 */

/**
 * @template T
 * @typedef {import('../utils/fetch').FetchResult<T>} FetchResult
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

  /** @type {FetchResult<JSTORMetadata>} */
  const metadata = useAPIFetch(
    articleId ? urlPath`/api/jstor/articles/${articleId}` : null
  );

  /** @type {FetchResult<JSTORThumbnail>} */
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
  } else if (metadata.data?.content_status === 'no_content') {
    renderedError =
      'There is no content available for this item. To select an item within a journal or book, enter a link to a specific article or chapter.';
  } else if (metadata.data?.content_status === 'no_access') {
    renderedError = 'Your institution does not have access to this item.';
  }

  const inputRef = /** @type {{ current: HTMLInputElement }} */ (useRef());
  // The last confirmed value of the URL-entry text input
  const previousURL = useRef(/** @type {string|null} */ (null));

  const canConfirmSelection =
    articleId &&
    metadata.data !== null &&
    metadata.data.content_status === 'available';

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

    const articleId = articleIdFromUserInput(url);
    if (!articleId) {
      setError("That doesn't look like a JSTOR article link or ID");
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
          Accept and continue
        </LabeledButton>,
      ]}
    >
      <div className="flex flex-row space-x-2">
        <Thumbnail
          classes={classnames(
            // Customize Thumbnail to:
            //  - Make more use of available vertical space within the Modal
            //  - "Crop" thumbnail image vertically to allow it to be wider
            //
            // TODO: Remove this customization after shared `Thumbnail`/related
            // shared component refactors.
            //
            // Negative vertical margins allow thumbnail to use up more vertical
            // space in the containing Modal
            '-mb-12 -mt-2',
            // Narrower grey border/background
            '!p-2',
            // Set up object containment such that the child is always a
            // specific width, with a suggested but variable height
            'w-[200px] min-w-[200px] h-52'
          )}
          isLoading={isLoading}
        >
          {thumbnail.data && (
            <img
              className={classnames(
                // Set up object positioning to "top". Bottom of thumbnail
                // image is "cropped" as necesary to fit container.
                // Need `!` to override `Thumbnail` styling's object-position
                // rules
                '!object-cover object-top'
              )}
              alt="article thumbnail"
              src={thumbnail.data.image}
            />
          )}
        </Thumbnail>
        <div className="space-y-2 grow flex flex-col">
          <p>Paste a link to the JSTOR article you&apos;d like to use:</p>

          <TextInputWithButton>
            <TextInput
              inputRef={inputRef}
              name="jstorURL"
              onChange={() => onURLChange()}
              onInput={() => setArticleId(null)}
              onKeyDown={onKeyDown}
              placeholder="e.g. https://www.jstor.org/stable/1234"
              spellcheck={false}
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
              className="flex flex-row space-x-2"
              data-testid="selected-book"
            >
              {canConfirmSelection && (
                <Icon name="check" classes="text-green-success" />
              )}
              <div className="grow font-bold italic">{metadata.data.title}</div>
            </div>
          )}

          {metadata.data && canConfirmSelection && (
            <>
              <div className="grow" />
              <div className="self-stretch text-right px-1">
                <label htmlFor="accept-jstor-terms" className="grow text-right">
                  Your use of JSTOR indicates your acceptance of JSTOR&apos;s{' '}
                  <Link
                    href="https://about.jstor.org/terms/"
                    classes="underline hover:underline"
                    target="_blank"
                  >
                    Terms and Conditions of Use.
                  </Link>
                </label>
              </div>
            </>
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
