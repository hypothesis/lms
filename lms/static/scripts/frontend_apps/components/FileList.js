import { Icon, Table } from '@hypothesis/frontend-shared';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {import("preact").ComponentChildren} Children
 */

/**
 * @typedef FileListProps
 * @prop {File[]} files - List of file objects returned by the API
 * @prop {boolean} [isLoading] - Whether to show a loading indicator
 * @prop {File|null} selectedFile - The file within `files` which is currently selected
 * @prop {(f: File) => any} onSelectFile -
 *   Callback invoked when the user clicks on a file
 * @prop {(f: File) => any} onUseFile -
 *   Callback invoked when the user double-clicks a file to indicate that they want to use it
 * @prop {Children} [noFilesMessage] - component displayed when no files are available
 */

/**
 * List of the files within a single directory.
 *
 * @param {FileListProps} props
 */
export default function FileList({
  files,
  isLoading = false,
  selectedFile,
  onSelectFile,
  onUseFile,
  noFilesMessage,
}) {
  /** @param {string} isoString */
  const formatDate = isoString => new Date(isoString).toLocaleDateString();
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
