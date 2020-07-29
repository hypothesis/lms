/**
 * @typedef {import('../api-types').File} File
 */

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch
 * URL for a given document URL.
 */
export function contentItemForUrl(ltiLaunchUrl, documentUrl) {
  return {
    '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
    '@graph': [
      {
        '@type': 'LtiLinkItem',
        mediaType: 'application/vnd.ims.lti.v1.ltilink',
        url: `${ltiLaunchUrl}?url=${encodeURIComponent(documentUrl)}`,
      },
    ],
  };
}

/**
 * Return a JSON-LD `ContentItem` representation of the LTI activity launch
 * URL for a given LMS file
 *
 * @param {string} ltiLaunchUrl
 * @param {File} file
 */
export function contentItemForLmsFile(ltiLaunchUrl, file) {
  return {
    '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
    '@graph': [
      {
        '@type': 'LtiLinkItem',
        mediaType: 'application/vnd.ims.lti.v1.ltilink',
        url: `${ltiLaunchUrl}?canvas_file=true&file_id=${file.id}`,
      },
    ],
  };
}
