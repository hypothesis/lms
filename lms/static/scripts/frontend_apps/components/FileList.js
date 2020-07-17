import classnames from 'classnames';
import { Fragment, createElement } from 'preact';
import propTypes from 'prop-types';

import Spinner from './Spinner';
import Table from './Table';

/**
 * @typedef File
 * @prop {string} display_name - The filename
 * @prop {string} updated_at - An ISO date or date + time string
 */

/**
 * @typedef FileListProps
 * @prop {File[]} files - List of file objects returned by a `listFiles` call
 * @prop {boolean} [isLoading] - Whether to show a loading indicator
 * @prop {File|null} selectedFile - The file within `files` which is currently selected
 * @prop {(f: File) => any} [onSelectFile] -
 *   Callback invoked when the user clicks on a file
 * @prop {(f: File) => any} [onUseFile] -
 *   Callback invoked when the user double-clicks a file to indicate that they want to use it
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
      {isLoading && <Spinner className="FileList__spinner" />}
    </div>
  );
}

FileList.propTypes = {
  files: propTypes.arrayOf(propTypes.object),
  isLoading: propTypes.bool,
  selectedFile: propTypes.object,
  onSelectFile: propTypes.func,
  onUseFile: propTypes.func,
};
