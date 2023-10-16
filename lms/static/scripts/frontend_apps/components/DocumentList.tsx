import {
  DataTable,
  FileGenericIcon,
  FilePdfFilledIcon,
  FolderIcon,
  Scroll,
} from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';

import type { Document } from '../api-types';

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

/**
 * List of the documents
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
      case 'display_name':
        return (
          <div className="flex flex-row items-center gap-x-2">
            {document.type === 'Folder' ? (
              <FolderIcon className="w-5 h-5" />
            ) : document.type === 'Page' ? (
              <FileGenericIcon className="w-5 h-5" />
            ) : (
              <FilePdfFilledIcon className="w-5 h-5" />
            )}
            {document.display_name}
          </div>
        );
      case 'updated_at':
      default:
        return document.updated_at ? formatDate(document.updated_at) : '';
    }
  };

  return (
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
      />
    </Scroll>
  );
}
