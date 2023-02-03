import { apiCall, urlPath } from '../utils/api';

/**
 * @typedef {import('../config').ContentBannerConfig} ContentBannerConfig
 * @typedef {import('./client-rpc').ContentInfoConfig} ContentInfoConfig
 * @typedef {import('./client-rpc').ContentInfoLinks} ContentInfoLinks
 */

/**
 * @param {string} itemId
 */
function itemURL(itemId) {
  return `https://www.jstor.org/stable/${itemId}`;
}

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
   * @param {ContentBannerConfig} contentId
   */
  async fetch(contentId) {
    // This condition exists for when new content sources are added.
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    if (contentId.source !== 'jstor') {
      throw new Error('Unknown content source');
    }

    /** @type {import('../api-types').JSTORMetadata} */
    const metadata = await apiCall({
      authToken: this._authToken,
      path: urlPath`/api/jstor/articles/${contentId.itemId}`,
    });

    const links = /** @type ContentInfoLinks */ ({
      currentItem: itemURL(contentId.itemId),
    });

    if (metadata.related_items.next_id) {
      links.nextItem = itemURL(metadata.related_items.next_id);
    }

    if (metadata.related_items.previous_id) {
      links.previousItem = itemURL(metadata.related_items.previous_id);
    }

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
        title: metadata.item.title,
        subtitle: metadata.item.subtitle,
      },
      container: {
        title: metadata.container.title,
        subtitle: metadata.container.subtitle,
      },

      links,
    };

    return this._clientRPC.showContentInfo(contentInfo);
  }
}
