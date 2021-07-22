/** @typedef {import('../api-types').File} File */

/**
 * @typedef FileContent
 * @prop {'file'} type
 * @prop {File} file
 *
 * @typedef URLContent
 * @prop {'url'} type
 * @prop {string} url
 *
 * @typedef VitalSourceBookContent
 * @prop {'vitalsource'} type
 * @prop {string} bookID
 * @prop {string} cfi
 */

/**
 * Enumeration of the different types of content that may be used for an assignment.
 *
 * @typedef {FileContent|URLContent|VitalSourceBookContent} Content
 */

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch
 * URL for a given piece of content.
 *
 * This is used for the `content_items` field of the form submitted to the LMS
 * to configure the LTI launch URL for a new assignment. See
 * https://www.imsglobal.org/specs/lticiv1p0/specification.
 *
 * @param {string} ltiLaunchURL - Base URL for LTI assignment launches
 * @param {Content} content - The assignment content
 * @param {Record<string,string>} [extraParams] - Additional query params to add to the launch URL
 */
export function contentItemForContent(ltiLaunchURL, content, extraParams) {
  const params = { ...extraParams };
  switch (content.type) {
    case 'file':
      params.canvas_file = 'true';
      params.file_id = content.file.id;
      break;
    case 'url':
      params.url = content.url;
      break;
    case 'vitalsource':
      params.vitalsource_book = 'true';
      params.book_id = content.bookID;
      params.cfi = content.cfi;
      break;
  }

  const url = new URL(ltiLaunchURL);
  Object.entries(params).forEach(([key, value]) =>
    url.searchParams.append(key, value)
  );

  return {
    '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
    '@graph': [
      {
        '@type': 'LtiLinkItem',
        mediaType: 'application/vnd.ims.lti.v1.ltilink',
        url: url.toString(),
      },
    ],
  };
}
