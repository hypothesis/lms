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
  children?: ComponentChildren;
  error?: string;
  thumbnail?: ThumbnailData;
  inputRef: RefObject<HTMLInputElement | undefined>;
  urlPlaceholder?: string;
  onURLChange: (inputUrl: string) => void;
  label: string;
  defaultURL?: string;
};

/**
 * Wraps a URL input and a Thumbnail were some kind of preview related with that URL is supposed to be displayed.
 * It also allows to optionally provide the next props:
 *  * `children`: Optional extra content that will be rendered right below the URL input.
 *  * `error`: An error message that will be rendered right below the URL input.
 *             Text is in red and will include a CancelIcon.
 *  * `defaultURL`: An initial value for the URL input. Mostly useful for tests.
 */
export default function URLFormWithPreview({
  children,
  error,
  thumbnail,
  inputRef,
  urlPlaceholder,
  onURLChange,
  label,
  defaultURL,
}: URLFormWithPreviewProps) {
  const inputId = useUniqueId('url');
  const onChange = () => onURLChange(inputRef.current!.value);
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      onChange();
    }
  };
  const ratio = thumbnail?.orientation ?? 'square';

  return (
    <div className="flex flex-row space-x-2">
      <div
        className={classnames(
          // Negative vertical margins allow thumbnail to use up more vertical
          // space in the containing Modal
          'w-[200px] min-w-[200px]',
          {
            'h-[200px]': ratio === 'square', // Default
            'h-[120px]': ratio === 'landscape',
          }
        )}
      >
        <Thumbnail
          size="sm"
          loading={thumbnail?.isLoading}
          ratio={ratio === 'square' ? '1/1' : '16/9'}
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
            placeholder={urlPlaceholder}
            spellcheck={false}
          />
          <IconButton
            icon={ArrowRightIcon}
            onClick={onChange}
            variant="dark"
            title="Find URL"
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
