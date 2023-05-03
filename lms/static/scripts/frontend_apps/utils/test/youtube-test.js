import { validateYouTubeVideoUrl, videoIdFromYouTubeUrl } from '../youtube';

describe('youtube', () => {
  describe('videoIdFromYouTubeUrl', () => {
    [
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
    ].forEach(({ url, expectedId }) => {
      it('resolves ID from valid YouTube video', () => {
        assert.equal(videoIdFromYouTubeUrl(url), expectedId);
      });
    });
  });

  describe('validateYouTubeVideoUrl', () => {
    [
      {
        url: 'foo',
        expectedError:
          'Please enter a YouTube URL, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"',
      },
      {
        url: 'file://foo',
        expectedError: 'Please use a URL that starts with "https"',
      },
      {
        url: 'https://example.com',
        expectedError: 'Please use a YouTube URL',
      },
      {
        url: 'https://youtube.com/watch',
        expectedError: 'Please, enter a URL for a specific YouTube video',
      },
      {
        url: 'https://youtu.be',
        expectedError: 'Please, enter a URL for a specific YouTube video',
      },
    ].forEach(({ url, expectedError }) => {
      it('throws an error when provided URL is not a valid YouTube video', () => {
        assert.throws(() => validateYouTubeVideoUrl(url), expectedError);
      });
    });

    [
      'https://youtu.be/cKxqzvzlnKU',
      'https://www.youtube.com/watch?v=cKxqzvzlnKU',
      'https://www.youtube.com/watch?channel=hypothesis&v=cKxqzvzlnKU',
      'https://www.youtube.com/embed/cKxqzvzlnKU',
    ].forEach(url => {
      it('does not throw when provided URL is a valid YouTube video', () => {
        assert.doesNotThrow(() => validateYouTubeVideoUrl(url));
      });
    });
  });
});
