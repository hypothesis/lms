import { contentItemForContent } from '../content-item';

const ltiLaunchURL = 'https://lms.hypothes.is/lti_launch';

describe('contentItemForContent', () => {
  [
    {
      content: { type: 'url', url: 'https://example.com?param_a=1&param_b=2' },
      expectedURL: `${ltiLaunchURL}?url=${encodeURIComponent(
        'https://example.com?param_a=1&param_b=2'
      )}`,
    },
    {
      content: { type: 'file', file: { id: 'foobar' } },
      expectedURL: `${ltiLaunchURL}?canvas_file=true&file_id=foobar`,
    },
  ].forEach(({ content, expectedURL }) => {
    it('returns JSON-LD representation for content', () => {
      const item = contentItemForContent(ltiLaunchURL, content);

      assert.deepEqual(item, {
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'LtiLinkItem',
            mediaType: 'application/vnd.ims.lti.v1.ltilink',
            url: expectedURL,
          },
        ],
      });
    });
  });

  it('adds extra query params to launch URL', () => {
    const item = contentItemForContent(
      ltiLaunchURL,
      { type: 'url', url: 'https://example.com' },
      { group_set: 'group1' }
    );
    const url = new URL(item['@graph'][0].url);
    assert.equal(url.searchParams.get('group_set'), 'group1');
  });
});
