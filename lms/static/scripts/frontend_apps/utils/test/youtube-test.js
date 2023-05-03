import { validateYouTubeVideUrl } from '../youtube';

describe('youtube', () => {
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
      assert.throws(() => validateYouTubeVideUrl(url), expectedError);
    });
  });

  [
    'https://youtu.be/cKxqzvzlnKU',
    'https://www.youtube.com/watch?v=cKxqzvzlnKU',
    'https://www.youtube.com/watch?channel=hypothesis&v=cKxqzvzlnKU',
    'https://www.youtube.com/embed/cKxqzvzlnKU',
  ].forEach(url => {
    it('does not throw when provided URL is a valid YouTube video', () => {
      assert.doesNotThrow(() => validateYouTubeVideUrl(url));
    });
  });
});
