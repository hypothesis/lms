/**
 * @typedef {import('../api-types').File} File
 */

import { stringify } from 'querystring';

/**
 * @param {string} ltiLaunchUrl
 * @param {Object.<string,string>} params - Query parameters for the generated URL
 */
function contentItemWithParams(ltiLaunchUrl, params) {
  return {
    '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
    '@graph': [
      {
        '@type': 'LtiLinkItem',
        mediaType: 'application/vnd.ims.lti.v1.ltilink',
        url: `${ltiLaunchUrl}?${stringify(params)}`,
      },
    ],
  };
}

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch
 * URL for a given document URL.
 *
 * @param {string} ltiLaunchUrl
 * @param {string} documentUrl
 */
export function contentItemForUrl(ltiLaunchUrl, documentUrl) {
  return contentItemWithParams(ltiLaunchUrl, { url: documentUrl });
}

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch
 * URL for a given LMS file
 *
 * @param {string} ltiLaunchUrl
 * @param {File} file
 */
export function contentItemForLmsFile(ltiLaunchUrl, file) {
  return contentItemWithParams(ltiLaunchUrl, {
    canvas_file: 'true',
    file_id: file.id,
  });
}

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch URL
 * for a VitalSource ebook.
 *
 * This currently just uses a hard-coded book ID and chapter specifier ("CFI").
 * In future the book ID and chapter will be parameters that are filled in with
 * a user's selection.
 *
 * @param {string} ltiLaunchUrl
 */
export function contentItemForVitalSourceBook(ltiLaunchUrl) {
  // Book ID from `GET https://api.vitalsource.com/v4/products` response.
  const bookId = 'BOOKSHELF-TUTORIAL';

  // CFI from `GET https://api.vitalsource.com/v4/products/BOOKSHELF-TUTORIAL/toc`
  // response.
  const chapterCfi =
    '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]';

  return contentItemWithParams(ltiLaunchUrl, {
    vitalsource_book: 'true',
    book_id: bookId,
    cfi: chapterCfi,
  });
}
