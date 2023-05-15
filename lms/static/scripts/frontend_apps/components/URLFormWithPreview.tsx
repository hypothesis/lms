import {
  ArrowRightIcon,
  CancelIcon,
  IconButton,
  Input,
  InputGroup,
  Thumbnail,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren, RefObject } from 'preact';

import { useUniqueId } from '../utils/hooks';

export type ThumbnailData = {
  image?: string;
  alt?: string;
  isLoading?: boolean;
  orientation?: 'square' | 'landscape';
};

export type URLFormWithPreviewProps = {
  /** Optional extra content to be rendered together with the input and thumbnail */
  children?: ComponentChildren;
  /** An error message to highlight that something went wrong */
  error?: string;
  /** Thumbnail info to be displayed, if known */
  thumbnail?: ThumbnailData;
  /** Reference to be set on the URL input */
  inputRef: RefObject<HTMLInputElement | undefined>;
  /** Invoked every time the input URL changes, with the value that was input */
  onURLChange: (inputURL: string) => void;
  label: string;
  /** Value to be set as "title" on the confirm button */
  confirmBtnTitle: string;
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
  label,
  confirmBtnTitle,
  urlPlaceholder,
  defaultURL,
}: URLFormWithPreviewProps) {
  const orientation = thumbnail?.orientation ?? 'square';
  const inputId = useUniqueId('url');
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
            onInput={() => onURLChange('')}
            onKeyDown={onKeyDown}
            placeholder={urlPlaceholder}
            spellcheck={false}
          />
          <IconButton
            icon={ArrowRightIcon}
            onClick={onChange}
            variant="dark"
            title={confirmBtnTitle}
          />
        </InputGroup>

        {children}

        {error && (
          <div
            className="flex flex-row items-center space-x-2 text-red-error"
            data-testid="error-message"
          >
            <CancelIcon />
            <div className="grow">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
