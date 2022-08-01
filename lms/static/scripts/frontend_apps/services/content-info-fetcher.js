import { apiCall, urlPath } from '../utils/api';

/**
 * @typedef {import('./client-rpc').ContentInfoConfig} ContentInfoConfig
 */

/**
 * Identifies the metadata provider and item ID for the content being displayed.
 *
 * @typedef ContentId
 * @prop {string} source
 * @prop {string} itemId
 */

/**
 * Service that fetches metadata and links for the Hypothesis client's content
 * information banner.
 *
 * Fetching metadata usually involves requests to third-party APIs. Since the
 * content information banner is a non-critical feature for the user, this
 * should be done concurrently with other activity needed to launch the
 * assignment, and shouldn't prevent the user from interacting with the
 * assignment if it fails. Instead the user just won't see the banner.
 */
export class ContentInfoFetcher {
  /**
   * @param {string} authToken
   * @param {import('./index').ClientRPC} clientRPC - Service for communicating
   *   with Hypothesis client
   */
  constructor(authToken, clientRPC) {
    this._authToken = authToken;
    this._clientRPC = clientRPC;
  }

  /**
   * Fetch metadata for content and send it to the client for display in the
   * content info banner.
   *
   * @param {ContentId} contentId
   */
  async fetch(contentId) {
    if (contentId.source !== 'jstor') {
      throw new Error('Unknown content source');
    }

    /** @type {import('../api-types').JSTORMetadata} */
    const metadata = await apiCall({
      authToken: this._authToken,
      path: urlPath`/api/jstor/articles/${contentId.itemId}`,
    });

    /** @type {ContentInfoConfig} */
    const contentInfo = {
      logo: {
        logo: new URL(
          '/static/images/jstor-logo.svg',
          location.href
        ).toString(),
        title: 'JSTOR homepage',
        link: 'https://www.jstor.org',
      },
      item: {
        title: metadata.title,

        // TODO - Fill in this information from the API
        containerTitle: '',
      },

      // TODO - Fill in these links from the API
      links: {},
    };

    return this._clientRPC.showContentInfo(contentInfo);
  }
}
