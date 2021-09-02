import { SvgIcon, Table } from '@hypothesis/frontend-shared';

import classnames from 'classnames';

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
      classes: 'FileList__date-header',
    },
  ];

  return (
    <>
      {!isLoading && files.length === 0 ? (
        noFilesMessage
      ) : (
        <Table
          accessibleLabel="File list"
          classes="FileList"
          tableHeaders={columns}
          isLoading={isLoading}
          items={files}
          selectedItem={selectedFile}
          onSelectItem={onSelectFile}
          onUseItem={onUseFile}
          renderItem={(file, isSelected) => (
            <>
              <td aria-label={file.display_name}>
                <div className="hyp-u-layout-row--center hyp-u-horizontal-spacing hyp-u-padding--left--2">
                  <SvgIcon
                    inline
                    name={
                      file.type && file.type === 'Folder' ? 'folder' : 'pdf'
                    }
                    className={classnames('FileList__icon', {
                      'is-selected': isSelected,
                    })}
                  />
                  <span className="u-stretch u-overflow--ellipsis">
                    {file.display_name}
                  </span>
                </div>
              </td>
              <td>{file.updated_at && formatDate(file.updated_at)}</td>
            </>
          )}
        />
      )}
    </>
  );
}
