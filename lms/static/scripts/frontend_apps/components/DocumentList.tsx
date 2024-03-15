import {
  DataTable,
  FileGenericIcon,
  FilePdfFilledIcon,
  FolderIcon,
  PreviewIcon,
  Scroll,
  ScrollContainer,
} from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import type { JSX } from 'preact';

import type { Document, MimeType } from '../api-types';

export type DocumentListProps<DocumentType extends Document> = {
  /** List of document objects returned by the API */
  documents: DocumentType[];
  /** Whether to show a loading indicator */
  isLoading?: boolean;
  /** The document within `documents` which is currently selected */
  selectedDocument: DocumentType | null;
  /** Callback invoked when the user clicks on a document */
  onSelectDocument: (doc: DocumentType | null) => void;
  /**
   * Callback invoked when the user double-clicks a document to indicate that
   * they want to use it
   */
  onUseDocument: (d: DocumentType | null) => void;
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

/**
 * List of files and folders in a file picker.
 */
export default function DocumentList<DocumentType extends Document>({
  documents,
  isLoading = false,
  selectedDocument,
  onSelectDocument,
  onUseDocument,
  noDocumentsMessage,
  title,
}: DocumentListProps<DocumentType>) {
  const formatDate = (isoString: string) =>
    new Date(isoString).toLocaleDateString();
  const columns = [
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

  const renderItem = (document: DocumentType, field: keyof DocumentType) => {
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
        return (
          <div className="flex flex-row items-center gap-x-2">
            <Icon className="w-5 h-5" />
            {document.display_name}
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
