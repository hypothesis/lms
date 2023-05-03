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

type ThumbnailData = {
  image?: string;
  alt?: string;
  isLoading?: boolean;
};

export type URLFormWithPreviewProps = {
  children?: ComponentChildren;
  thumbnail?: ThumbnailData;
  error?: string;
  inputRef: RefObject<HTMLInputElement | undefined>;
  urlPlaceholder?: string;
  onURLChange: (inputUrl: string) => void;
  label: string;
  defaultURL?: string;
};

export default function URLFormWithPreview({
  children,
  thumbnail,
  error,
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

  return (
    <div className="flex flex-row space-x-2">
      <div
        className={classnames(
          // Negative vertical margins allow thumbnail to use up more vertical
          // space in the containing Modal
          '-mb-12 -mt-2 w-[200px] min-w-[200px] h-[200px]'
        )}
      >
        <Thumbnail size="sm" loading={thumbnail?.isLoading} ratio="1/1">
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
            title="Find article"
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
