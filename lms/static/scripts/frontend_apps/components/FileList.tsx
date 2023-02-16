import {
  DataTable,
  FilePdfFilledIcon,
  FolderIcon,
  Scroll,
} from '@hypothesis/frontend-shared/lib/next';
import type { ComponentChildren } from 'preact';

import type { File } from '../api-types';

export type FileListProps = {
  /** List of file objects returned by the API */
  files: File[];
  /** Whether to show a loading indicator */
  isLoading?: boolean;
  /** The file within `files` which is currently selected */
  selectedFile: File | null;
  /** Callback invoked when the user clicks on a file */
  onSelectFile: (f: File) => void;
  /**
   * Callback invoked when the user double-clicks a file to indicate that they
   * want to use it
   */
  onUseFile: (f: File) => void;
  /** Optional message to display if there are no files */
  noFilesMessage?: ComponentChildren;
};

/**
 * List of the files within a single directory.
 */
export default function FileList({
  files,
  isLoading = false,
  selectedFile,
  onSelectFile,
  onUseFile,
  noFilesMessage,
}: FileListProps) {
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

  const renderItem = (file: File, field: keyof File) => {
    switch (field) {
      case 'display_name':
        return (
          <div className="flex flex-row items-center gap-x-2">
            {file.type === 'Folder' ? (
              <FolderIcon className="w-5 h-5" />
            ) : (
              <FilePdfFilledIcon className="w-5 h-5" />
            )}
            {file.display_name}
          </div>
        );
      case 'updated_at':
      default:
        return file.updated_at ? formatDate(file.updated_at) : '';
    }
  };

  return (
    <Scroll>
      <DataTable
        title="File list"
        emptyMessage={noFilesMessage}
        columns={columns}
        loading={isLoading}
        rows={files}
        selectedRow={selectedFile}
        onSelectRow={onSelectFile}
        onConfirmRow={onUseFile}
        renderItem={renderItem}
      />
    </Scroll>
  );
}
