import {
  ArrowRightIcon,
  IconButton,
  Input,
  InputGroup,
  Thumbnail,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren, RefObject } from 'preact';
import { useId } from 'preact/hooks';

import { useUniqueId } from '../utils/hooks';
import ErrorMessage from './ErrorMessage';

export type ThumbnailData = {
  image?: string;
  alt?: string;
  isLoading?: boolean;
  orientation?: 'square' | 'landscape';
};

export type URLFormWithPreviewProps = {
  /** Optional extra content to be rendered together with the input and thumbnail */
  children?: ComponentChildren;
  /** Error content to highlight that something went wrong */
  error?: ComponentChildren;
  /** Thumbnail info to be displayed, if known */
  thumbnail?: ThumbnailData;
  /** Reference to be set on the URL input */
  inputRef: RefObject<HTMLInputElement | undefined>;
  /** Invoked every time the input URL changes, with the value that was input */
  onURLChange: (inputURL: string) => void;
  /** Invoked when the input content is modified */
  onInput: () => void;
  label: string;
  urlPlaceholder?: string;
  defaultURL?: string;
};

/**
 * Wraps a URL input and a preview of the content available at the entered URL.
 */
export default function URLFormWithPreview({
  children,
  error,
  thumbnail,
  inputRef,
  onURLChange,
  onInput,
  label,
  urlPlaceholder,
  defaultURL,
}: URLFormWithPreviewProps) {
  const orientation = thumbnail?.orientation ?? 'square';
  const inputId = useUniqueId('url');
  const errorId = useId();
  const onChange = () => onURLChange(inputRef.current!.value);
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      onChange();
    }
  };

  return (
    <div className="flex flex-row space-x-2">
      <div
        className={classnames(
          // Negative vertical margins allow thumbnail to use up more vertical
          // space in the containing Modal
          'w-[200px] min-w-[200px]',
          {
            'h-[200px]': orientation === 'square', // Default
            'h-[120px]': orientation === 'landscape',
          }
        )}
      >
        <Thumbnail
          size="sm"
          loading={thumbnail?.isLoading}
          ratio={orientation === 'square' ? '1/1' : '16/9'}
        >
          {thumbnail?.image && (
            <img
              className={classnames(
                // Set up object positioning to "top". Bottom of thumbnail
                // image is "cropped" as necessary to fit container.
                'object-top'
              )}
              alt={thumbnail.alt}
              src={thumbnail.image}
            />
          )}
        </Thumbnail>
      </div>
      <div className="space-y-2 grow flex flex-col">
        <p>
          <label htmlFor={inputId}>{label}</label>
        </p>

        <InputGroup>
          <Input
            defaultValue={defaultURL}
            elementRef={inputRef}
            id={inputId}
            name="URL"
            onChange={onChange}
            onKeyDown={onKeyDown}
            onInput={onInput}
            placeholder={urlPlaceholder}
            spellcheck={false}
            aria-labelledby={errorId}
          />
          <IconButton
            icon={ArrowRightIcon}
            onClick={onChange}
            variant="dark"
            title="Confirm URL"
          />
        </InputGroup>

        {children}

        <ErrorMessage error={error} id={errorId} data-testid="error-message" />
      </div>
    </div>
  );
}
