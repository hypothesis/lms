import { contentItemForUrl, contentItemForLmsFile } from '../content-item';

const ltiLaunchUrl = 'https://lms.hypothes.is/lti_launch';

describe('content-item', () => {
  describe('contentItemForUrl', () => {
    it('returns expected JSON-LD representation', () => {
      const documentUrl = 'https://example.com?param_a=1&param_b=2';

      const contentItem = contentItemForUrl(ltiLaunchUrl, documentUrl);

      assert.deepEqual(contentItem, {
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'LtiLinkItem',
            mediaType: 'application/vnd.ims.lti.v1.ltilink',
            url: ltiLaunchUrl + '?url=' + encodeURIComponent(documentUrl),
          },
        ],
      });
    });
  });

  describe('contentItemForLmsFile', () => {
    it('returns expected JSON-LD representation', () => {
      const file = { id: 'foobar' };

      const contentItem = contentItemForLmsFile(ltiLaunchUrl, file);

      assert.deepEqual(contentItem, {
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'LtiLinkItem',
            mediaType: 'application/vnd.ims.lti.v1.ltilink',
            url: ltiLaunchUrl + '?canvas_file=true&file_id=foobar',
          },
        ],
      });
    });
  });
});
