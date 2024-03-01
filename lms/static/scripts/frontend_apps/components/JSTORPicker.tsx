import {
  ArrowRightIcon,
  Button,
  IconButton,
  Input,
  InputGroup,
  Link,
  ModalDialog,
  Thumbnail,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useId, useRef, useState } from 'preact/hooks';

import type { JSTORMetadata, JSTORThumbnail } from '../api-types';
import { formatErrorMessage } from '../errors';
import { urlPath, useAPIFetch } from '../utils/api';
import type { FetchResult } from '../utils/fetch';
import { useUniqueId } from '../utils/hooks';
import { articleIdFromUserInput, jstorURLFromArticleId } from '../utils/jstor';
import UIMessage from './UIMessage';

export type JSTORPickerProps = {
  /**
   * Article to select when the picker is initially rendered.
   *
   * This can be a JSTOR article ID, DOI or stable URL.
   */
  defaultArticle?: string;

  onCancel: () => void;
  /** Callback to set the assignment's content to a JSTOR article URL */
  onSelectURL: (url: string) => void;
};

/**
 * A picker that allows a user to enter a URL corresponding to a JSTOR article.
 */
export default function JSTORPicker({
  defaultArticle,
  onCancel,
  onSelectURL,
}: JSTORPickerProps) {
  const [error, setError] = useState<string | null>(null);
  const errorId = useId();

  // Selected JSTOR article ID or DOI, updated when the user confirms what
  // they have pasted/typed into the input field.
  const [articleId, setArticleId] = useState<string | null>(
    defaultArticle ? articleIdFromUserInput(defaultArticle) : null,
  );

  const metadata: FetchResult<JSTORMetadata> = useAPIFetch(
    articleId ? urlPath`/api/jstor/articles/${articleId}` : null,
  );

  const thumbnail: FetchResult<JSTORThumbnail> = useAPIFetch(
    articleId ? urlPath`/api/jstor/articles/${articleId}/thumbnail` : null,
  );

  let renderedError;
  if (error) {
    renderedError = error;
  } else if (metadata.error) {
    renderedError = formatErrorMessage(
      metadata.error,
      'Unable to fetch article details',
    );
  } else if (metadata.data?.content_status === 'no_content') {
    renderedError =
      'There is no content available for this item. To select an item within a journal or book, enter a link to a specific article or chapter.';
  } else if (metadata.data?.content_status === 'no_access') {
    renderedError = 'Your institution does not have access to this item.';
  }

  const inputRef = useRef<HTMLInputElement | null>(null);
  // The last confirmed value of the URL-entry text input
  const previousURL = useRef<string | null>(null);
  const inputId = useUniqueId('jstor-article-id');

  const canConfirmSelection =
    articleId &&
    metadata.data !== null &&
    metadata.data.content_status === 'available';

  const confirmSelection = () => {
    if (canConfirmSelection) {
      onSelectURL(jstorURLFromArticleId(articleId));
    }
  };

  const onURLChange = (confirmSelectedUrl = false) => {
    const url = inputRef.current!.value;
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
   */
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      onURLChange(true /* confirmSelection */);
    }
  };

  const resetCurrentArticle = () => {
    previousURL.current = null;
    setArticleId(null);
  };

  const isLoading = thumbnail.isLoading || metadata.isLoading;

  return (
    <ModalDialog
      initialFocus={inputRef}
      onClose={onCancel}
      closeTitle="Close JSTOR picker"
      scrollable={false}
      title="Select JSTOR article"
      size="lg"
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="select-button"
          disabled={!canConfirmSelection}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Accept and continue
        </Button>,
      ]}
    >
      <div className="flex flex-row space-x-2">
        <div
          className={classnames(
            // Negative vertical margins allow thumbnail to use up more vertical
            // space in the containing Modal
            '-mb-12 -mt-2 w-[200px] min-w-[200px] h-[200px]',
          )}
        >
          <Thumbnail size="sm" loading={isLoading} ratio="1/1">
            {thumbnail.data && (
              <img
                className={classnames(
                  // Set up object positioning to "top". Bottom of thumbnail
                  // image is "cropped" as necesary to fit container.
                  'object-top',
                )}
                alt="article thumbnail"
                src={thumbnail.data.image}
              />
            )}
          </Thumbnail>
        </div>
        <div className="space-y-2 grow flex flex-col">
          <p>
            <label htmlFor={inputId}>
              Paste a link to the JSTOR article you&apos;d like to use:
            </label>
          </p>

          <InputGroup>
            <Input
              defaultValue={defaultArticle}
              elementRef={inputRef}
              id={inputId}
              name="jstorURL"
              feedback={renderedError ? 'error' : undefined}
              onChange={() => onURLChange()}
              onInput={() => resetCurrentArticle()}
              onKeyDown={onKeyDown}
              placeholder="e.g. https://www.jstor.org/stable/1234"
              spellcheck={false}
              aria-describedby={errorId}
            />
            <IconButton
              icon={ArrowRightIcon}
              onClick={() => onURLChange()}
              variant="dark"
              title="Find article"
            />
          </InputGroup>

          {metadata.data && (
            <UIMessage
              status={canConfirmSelection ? 'success' : 'info'}
              data-testid="selected-book"
            >
              <span className="font-bold italic">
                {metadata.data.item.title}
                {metadata.data.item.subtitle && (
                  <>: {metadata.data.item.subtitle}</>
                )}
              </span>
            </UIMessage>
          )}

          {metadata.data && canConfirmSelection && (
            <>
              <div className="grow" />
              <div className="self-stretch text-right px-1">
                <label htmlFor="accept-jstor-terms" className="grow text-right">
                  Your use of JSTOR indicates your acceptance of JSTOR&apos;s{' '}
                  <Link
                    classes="whitespace-nowrap"
                    href="https://about.jstor.org/terms/"
                    target="_blank"
                    underline="always"
                  >
                    Terms and Conditions of Use.
                  </Link>
                </label>
              </div>
            </>
          )}

          {renderedError && (
            <UIMessage status="error" id={errorId}>
              {renderedError}
            </UIMessage>
          )}
        </div>
      </div>
    </ModalDialog>
  );
}
