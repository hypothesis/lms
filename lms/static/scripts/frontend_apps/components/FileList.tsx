import { Icon, Table } from '@hypothesis/frontend-shared';
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
    },
    {
      label: 'Last modified',
      classes: 'w-32',
    },
  ];

  return (
    <Table
      accessibleLabel="File list"
      emptyItemsMessage={noFilesMessage}
      tableHeaders={columns}
      isLoading={isLoading}
      items={files}
      selectedItem={selectedFile}
      onSelectItem={onSelectFile}
      onUseItem={onUseFile}
      renderItem={file => (
        <>
          <td aria-label={file.display_name}>
            <div className="flex flex-row items-center space-x-2">
              <Icon
                name={file.type && file.type === 'Folder' ? 'folder' : 'pdf'}
                classes="w-5 h-5"
              />
              <div className="grow leading-snug">{file.display_name}</div>
            </div>
          </td>
          <td>{file.updated_at && formatDate(file.updated_at)}</td>
        </>
      )}
    />
  );
}
