import { Fragment, createElement } from 'preact';

import {
  contentItemForUrl,
  contentItemForLmsFile,
  contentItemForVitalSourceBook,
} from '../utils/content-item';

/**
 * @typedef {import('./ContentSelector').Content} Content
 * @typedef {import('./GroupSetSelector').GroupConfig} Grouping
 */

/**
 * @typedef LTIContentItemFormFieldsProps
 * @prop {string} ltiLaunchURL
 * @prop {Content} content
 * @prop {Record<string,string>} formFields
 * @prop {Grouping} grouping
 */

/**
 * Generate an LTI launch URL for a given.
 *
 * @param {string} ltiLaunchURL
 * @param {Content|null} content
 * @param {Grouping} grouping
 */
function contentItemString(ltiLaunchURL, content, grouping) {
  let contentItem = null;
  const options = {};
  if (grouping.useGroups && grouping.groupSet) {
    options.groupSet = grouping.groupSet;
  }

  switch (content?.type) {
    case 'url':
      contentItem = contentItemForUrl(ltiLaunchURL, content.url, options);
      break;
    case 'file':
      contentItem = contentItemForLmsFile(ltiLaunchURL, content.file, options);
      break;
    case 'vitalsource': {
      // Chosen from `https://api.vitalsource.com/v4/products` response.
      const bookId = 'BOOKSHELF-TUTORIAL';
      // CFI chosen from `https://api.vitalsource.com/v4/products/BOOKSHELF-TUTORIAL/toc`
      // response.
      const cfi =
        '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]';
      contentItem = contentItemForVitalSourceBook(
        ltiLaunchURL,
        bookId,
        cfi,
        options
      );
    }
  }
  return JSON.stringify(contentItem);
}

/**
 * Render the hidden form fields containing information about the selected
 * content and other assignments.
 *
 * @param {LTIContentItemFormFieldsProps} props
 */
export default function LTIContentItemFormFields({
  ltiLaunchURL,
  content,
  formFields,
  grouping,
}) {
  return (
    <Fragment>
      <input
        type="hidden"
        name="content_items"
        value={contentItemString(ltiLaunchURL, content, grouping)}
      />
      {Object.keys(formFields).map(field => (
        <input
          key={field}
          type="hidden"
          name={field}
          value={formFields[field]}
        />
      ))}
      {content?.type === 'url' && (
        <input name="document_url" type="hidden" value={content.url} />
      )}
    </Fragment>
  );
}
