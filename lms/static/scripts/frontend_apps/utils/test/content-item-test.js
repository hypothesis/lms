import {
  contentItemForUrl,
  contentItemForLmsFile,
  contentItemForVitalSourceBook,
} from '../content-item';

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

  describe('contentItemForVitalSourceBook', () => {
    it('returns expected JSON-LD data', () => {
      const bookId = 'TEST-BOOK';
      const chapterCfi = '/4/5';

      const contentItem = contentItemForVitalSourceBook(
        ltiLaunchUrl,
        bookId,
        chapterCfi
      );

      assert.deepEqual(contentItem, {
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'LtiLinkItem',
            mediaType: 'application/vnd.ims.lti.v1.ltilink',
            url:
              ltiLaunchUrl +
              '?vitalsource_book=true&book_id=TEST-BOOK&cfi=%2F4%2F5',
          },
        ],
      });
    });
  });
});
