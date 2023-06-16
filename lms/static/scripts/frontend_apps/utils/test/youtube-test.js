import { isYouTubeURL, videoIdFromYouTubeURL } from '../youtube';

describe('youtube', () => {
  const validURLs = [
    { url: 'https://youtu.be/cKxqzvzlnKU', expectedId: 'cKxqzvzlnKU' },
    { url: 'https://www.youtube.com/watch?v=123', expectedId: '123' },
    {
      url: 'https://www.youtube.com/watch?channel=hypothesis&v=foo',
      expectedId: 'foo',
    },
    {
      url: 'https://www.youtube.com/embed/embeddedId',
      expectedId: 'embeddedId',
    },
    {
      url: 'https://www.youtube.com/shorts/shortId',
      expectedId: 'shortId',
    },
    {
      url: 'https://www.youtube.com/live/liveId?feature=share',
      expectedId: 'liveId',
    },
  ];
  const invalidURLs = [
    'foo',
    'file://foo',
    'https://example.com',
    'https://youtube.com/watch',
    'https://youtu.be',
  ];

  describe('videoIdFromYouTubeURL', () => {
    validURLs.forEach(({ url, expectedId }) => {
      it('resolves ID from valid YouTube video', () => {
        assert.equal(videoIdFromYouTubeURL(url), expectedId);
      });
    });

    invalidURLs.forEach(url => {
      it('returns null for invalid YouTube videos', () => {
        assert.isNull(videoIdFromYouTubeURL(url));
      });
    });
  });

  describe('isYouTubeURL', () => {
    validURLs.forEach(({ url }) => {
      it('returns true for valid YouTube video', () => {
        assert.isTrue(isYouTubeURL(url));
      });
    });

    invalidURLs.forEach(url => {
      it('returns false for invalid YouTube videos', () => {
        assert.isFalse(isYouTubeURL(url));
      });
    });
  });
});
