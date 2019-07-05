import classnames from 'classnames';
import { Fragment, createElement } from 'preact';
import propTypes from 'prop-types';

import Spinner from './Spinner';
import Table from './Table';

/**
 * List of the files within a single directory.
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
        columns={columns}
        items={files}
        selectedItem={selectedFile}
        onSelectItem={onSelectFile}
        onUseItem={onUseFile}
        renderItem={(file, isSelected) => (
          <Fragment>
            <td className="FileList__name-col">
              <img
                className={classnames(
                  'FileList__icon',
                  isSelected && 'is-selected'
                )}
                src="/static/images/file-pdf.svg"
                alt="PDF icon"
              />
              <a href="#" className="FileList__name">
                {file.display_name}
              </a>
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
  /** List of file objects returned by a `listFiles` call. */
  files: propTypes.arrayOf(propTypes.object),

  /** Whether to show a loading indicator. */
  isLoading: propTypes.bool,

  /** The file within `files` which is currently selected. */
  selectedFile: propTypes.object,

  /**
   * Callback passed the selected file when the user clicks on a file in
   * order to select it before performing further actions on it.
   */
  onSelectFile: propTypes.func,

  /**
   * Callback passed when the user double-clicks a file to indicate that they
   * want to use it.
   */
  onUseFile: propTypes.func,
};
