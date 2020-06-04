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
 * @param {string} ltiLaunchUrl
 * @param {string} bookId - VitalSource book ID (aka. `vbid`)
 * @param {string} cfi -
 *   Location in the book. This is an EPUB CFI path without the surrounding
 *   `epubcfi(...)` fragment. See http://idpf.org/epub/linking/cfi/epub-cfi.html.
 */
export function contentItemForVitalSourceBook(ltiLaunchUrl, bookId, cfi) {
  return contentItemWithParams(ltiLaunchUrl, {
    vitalsource_book: 'true',
    book_id: bookId,
    cfi,
  });
}
