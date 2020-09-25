import classnames from 'classnames';
import { Fragment, createElement } from 'preact';

import Spinner from './Spinner';
import Table from './Table';

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
  const formatDate = isoString => new Date(isoString).toLocaleDateString();
  const columns = [
    {
      label: 'Name',
      className: 'FileList__name-header',
    },
    {
      label: 'Last modified',
      className: 'FileList__date-header',
    },
  ];

  return (
    <div className="FileList">
      <Table
        accessibleLabel="File list"
        columns={columns}
        items={files}
        selectedItem={selectedFile}
        onSelectItem={onSelectFile}
        onUseItem={onUseFile}
        renderItem={(file, isSelected) => (
          <Fragment>
            <td aria-label={file.display_name} className="FileList__name-col">
              <img
                className={classnames(
                  'FileList__icon',
                  isSelected && 'is-selected'
                )}
                src="/static/images/file-pdf.svg"
                alt="PDF icon"
              />
              <span className="FileList__name">{file.display_name}</span>
            </td>
            <td className="FileList__date-col">
              {file.updated_at && formatDate(file.updated_at)}
            </td>
          </Fragment>
        )}
      />
      {!isLoading && files.length === 0 && noFilesMessage}
      {isLoading && <Spinner className="FileList__spinner" />}
    </div>
  );
}
