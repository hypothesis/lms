import type { JSTORMetadata } from '../api-types';
import type { ContentBannerConfig } from '../config';
import { apiCall, urlPath } from '../utils/api';
import type { ContentInfoConfig, ContentInfoLinks } from './client-rpc';
import type { ClientRPC } from './index';

function itemURL(itemId: string) {
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
  private _authToken: string;
  private _clientRPC: ClientRPC;

  /**
   * @param clientRPC - Service for communicating with Hypothesis client
   */
  constructor(authToken: string, clientRPC: ClientRPC) {
    this._authToken = authToken;
    this._clientRPC = clientRPC;
  }

  /**
   * Fetch metadata for content and send it to the client for display in the
   * content info banner.
   */
  async fetch(contentId: ContentBannerConfig) {
    // This condition exists for when new content sources are added.
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    if (contentId.source !== 'jstor') {
      throw new Error('Unknown content source');
    }

    const metadata = await apiCall<JSTORMetadata>({
      authToken: this._authToken,
      path: urlPath`/api/jstor/articles/${contentId.itemId}`,
    });

    const links: ContentInfoLinks = {
      currentItem: itemURL(contentId.itemId),
    };

    if (metadata.related_items.next_id) {
      links.nextItem = itemURL(metadata.related_items.next_id);
    }

    if (metadata.related_items.previous_id) {
      links.previousItem = itemURL(metadata.related_items.previous_id);
    }

    const contentInfo: ContentInfoConfig = {
      logo: {
        logo: new URL(
          '/static/images/jstor-logo.svg',
          location.href,
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
