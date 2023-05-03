import { InvalidArgumentError } from '../errors';

type YouTubeURL = string;

/**
 * Tries to match provided URL against known YouTube video URL formats,
 * throwing an error in case of invalid YouTube URL
 */
export function validateYouTubeVideUrl(
  youTubeUrl: string
): asserts youTubeUrl is YouTubeURL {
  let url;
  try {
    url = new URL(youTubeUrl);
  } catch (e) {
    throw new InvalidArgumentError(
      'Please enter a YouTube URL, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"'
    );
  }

  if (!url.protocol.startsWith('https')) {
    throw new InvalidArgumentError('Please use a URL that starts with "https"');
  }

  if (!['www.youtube.com', 'youtube.com', 'youtu.be'].includes(url.host)) {
    throw new InvalidArgumentError('Please use a YouTube URL');
  }

  // This regexp tries to match the video ID in the next possible URLs
  //  * youtu.be/{id}
  //  * {domain}/watch?v={id}[...]
  //  * {domain}/embed/{id}[...]
  // See https://stackoverflow.com/a/9102270 for details
  const match = youTubeUrl.match(
    /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
  );
  if (!match?.[2]) {
    throw new InvalidArgumentError(
      'Please, enter a URL for a specific YouTube video'
    );
  }
}
