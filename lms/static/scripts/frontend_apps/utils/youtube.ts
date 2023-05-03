import { InvalidArgumentError } from '../errors';

/**
 * Tries to resolve the video ID from a YouTube URL
 * @return Undefined if the ID could not be resolved
 */
export function videoIdFromYouTubeUrl(youTubeUrl: string): string | undefined {
  // This regexp tries to match the video ID in the next possible URLs
  //  * youtu.be/{id}
  //  * {domain}/watch?v={id}[...]
  //  * {domain}/embed/{id}[...]
  // See https://stackoverflow.com/a/9102270 for details
  const match = youTubeUrl.match(
    /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
  );

  return match?.[2];
}

/**
 * Tries to match provided URL against known YouTube video URL formats,
 * throwing an error in case of invalid YouTube URL
 */
export function validateYouTubeVideUrl(youTubeUrl: string): string {
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

  const videoId = videoIdFromYouTubeUrl(youTubeUrl);
  if (!videoId) {
    throw new InvalidArgumentError(
      'Please, enter a URL for a specific YouTube video'
    );
  }

  return videoId;
}
