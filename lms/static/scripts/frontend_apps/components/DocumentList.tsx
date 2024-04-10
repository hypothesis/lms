import {
  DataTable,
  FileGenericIcon,
  FilePdfFilledIcon,
  FolderIcon,
  PreviewIcon,
  Scroll,
  ScrollContainer,
} from '@hypothesis/frontend-shared';
import type { DataTableProps } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import type { JSX } from 'preact';
import { useMemo, useState } from 'preact/hooks';

import type { File, Folder, MimeType } from '../api-types';

export type DocumentListProps = {
  /** List of document objects returned by the API */
  documents: Array<File | Folder>;
  /** Whether to show a loading indicator */
  isLoading?: boolean;
  /** The document within `documents` which is currently selected */
  selectedDocument: File | Folder | null;
  /** Callback invoked when the user clicks on a document */
  onSelectDocument: (doc: File | Folder | null) => void;
  /**
   * Callback invoked when the user double-clicks a document to indicate that
   * they want to use it
   */
  onUseDocument: (d: File | Folder | null) => void;
  /** Optional message to display if there are no documents */
  noDocumentsMessage?: ComponentChildren;
  /** Component title for accessibility */
  title: string;
};

type IconComponent = (props: { className?: string }) => JSX.Element;

const mimeTypeIcons: Record<MimeType, IconComponent> = {
  'application/pdf': FilePdfFilledIcon,
  'text/html': FileGenericIcon,
  video: PreviewIcon,
};

type FileThumbnailProps = {
  src: string;
  fallback: ComponentChildren;
  duration?: number;
};

/**
 * Display a media thumbnail with a fallback if the content fails to load.
 *
 * The fallback exists because the thumbnail URLs may refer to images hosted
 * on third-party servers, so we can't be sure they will return valid images.
 * The alternative would be to proxy all thumbnails through the LMS's server,
 * which could serve a fallback if upstream fails to load.
 */
function FileThumbnail({ src, fallback, duration }: FileThumbnailProps) {
  const [useFallback, setUseFallback] = useState(false);
  const formattedDuration = useMemo(
    () => (typeof duration === 'number' ? formatDuration(duration) : null),
    [duration],
  );

  return (
    <div className="min-w-[96px] min-h-[54px] flex items-center justify-center relative rounded bg-grey-3 overflow-clip">
      {!useFallback && (
        <img
          className="w-[96px]"
          data-testid="thumbnail"
          alt=""
          onError={() => setUseFallback(true)}
          src={src}
        />
      )}
      {useFallback && <div data-testid="thumbnail-fallback">{fallback}</div>}
      {formattedDuration && (
        <div
          className="absolute bottom-0 right-0 text-grey-1 bg-grey-9/75 px-1 rounded"
          data-testid="duration"
        >
          {formattedDuration}
        </div>
      )}
    </div>
  );
}

/** Format a duration in seconds as an `MM:SS` string. */
function formatDuration(duration: number): string {
  const mins = Math.floor(duration / 60);
  const secs = Math.round(duration % 60);
  return (
    mins.toString().padStart(2, '0') + ':' + secs.toString().padStart(2, '0')
  );
}

/**
 * List of files and folders in a file picker.
 */
export default function DocumentList({
  documents,
  isLoading = false,
  selectedDocument,
  onSelectDocument,
  onUseDocument,
  noDocumentsMessage,
  title,
}: DocumentListProps) {
  const formatDate = (isoString: string) =>
    new Date(isoString).toLocaleDateString();
  const columns: DataTableProps<File | Folder>['columns'] = [
    {
      label: 'Name',
      field: 'display_name',
    },
    {
      label: 'Last modified',
      field: 'updated_at',
      classes: 'w-32',
    },
  ];

  const renderItem = (
    document: File | Folder,
    field: keyof (File | Folder),
  ) => {
    switch (field) {
      case 'display_name': {
        let Icon;
        if (document.type === 'Folder') {
          Icon = FolderIcon;
        } else if (document.mime_type) {
          Icon = mimeTypeIcons[document.mime_type];
        } else {
          Icon = FileGenericIcon;
        }
        const icon = <Icon data-testid="icon" className="w-5 h-5" />;

        let thumbnail;
        if (document.type === 'File' && document.thumbnail_url) {
          thumbnail = (
            <FileThumbnail
              src={document.thumbnail_url}
              fallback={icon}
              duration={document.duration}
            />
          );
        }

        return (
          <div className="flex flex-row items-center gap-x-2">
            {thumbnail ?? icon}
            <span data-testid="display-name">{document.display_name}</span>
          </div>
        );
      }
      case 'updated_at':
      default:
        return document.updated_at ? formatDate(document.updated_at) : '';
    }
  };

  return (
    <ScrollContainer rounded>
      <Scroll>
        <DataTable
          title={title}
          emptyMessage={noDocumentsMessage}
          columns={columns}
          loading={isLoading}
          rows={documents}
          selectedRow={selectedDocument}
          onSelectRow={onSelectDocument}
          onConfirmRow={onUseDocument}
          renderItem={renderItem}
          borderless
        />
      </Scroll>
    </ScrollContainer>
  );
}
