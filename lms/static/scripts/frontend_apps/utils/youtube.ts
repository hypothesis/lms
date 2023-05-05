import { useEffect, useState } from 'preact/hooks';

import type { ThumbnailData } from '../components/URLFormWithPreview';
import { InvalidArgumentError } from '../errors';

/**
 * Tries to resolve the video ID from a YouTube URL
 * @return Undefined if the ID could not be resolved
 */
export function videoIdFromYouTubeURL(url: string): string | undefined {
  // This regexp tries to match the video ID in the next possible URLs
  //  * youtu.be/{id}
  //  * {domain}/watch?v={id}[...]
  //  * {domain}/embed/{id}[...]
  //  * {domain}/shorts/{id}[...]
  //  * {domain}/live/{id}[...]
  // See https://stackoverflow.com/a/9102270 for details
  const match = url.match(
    /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|live\/|watch\?v=|&v=)([^#&?]*).*/
  );

  return match?.[2];
}

/**
 * Tries to match provided URL against known YouTube video URL formats,
 * throwing an error in case of invalid YouTube URL
 */
export function validateYouTubeVideoURL(url: string): string {
  let parsedURL;
  try {
    parsedURL = new URL(url);
  } catch (e) {
    throw new InvalidArgumentError(
      'Please enter a YouTube URL, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"'
    );
  }

  if (!parsedURL.protocol.startsWith('https')) {
    throw new InvalidArgumentError('Please use a URL that starts with "https"');
  }

  if (
    !['www.youtube.com', 'youtube.com', 'youtu.be'].includes(parsedURL.host)
  ) {
    throw new InvalidArgumentError('Please use a YouTube URL');
  }

  const videoId = videoIdFromYouTubeURL(url);
  if (!videoId) {
    throw new InvalidArgumentError(
      'Please, enter a URL for a specific YouTube video'
    );
  }

  return videoId;
}

/* istanbul ignore next */
export function useYouTubeVideoInfo(videoId?: string) {
  // TODO Use dummy data for now, until a proper API has been implemented
  const [thumbnail, setThumbnail] = useState<ThumbnailData>();
  const [metadata, setMetadata] = useState<{
    title: string;
    channel: string;
  }>();

  useEffect(() => {
    if (videoId) {
      setThumbnail({
        alt: 'Youtube video',
        image: 'https://i.ytimg.com/vi/EU6TDnV5osM/mqdefault.jpg',
        isLoading: false,
        orientation: 'landscape',
      });
      setMetadata({
        title:
          'Hypothesis and Atlassian New Partnership Announced at the Team23 Conference',
        channel: 'Hypothesis',
      });
    } else {
      setThumbnail(undefined);
      setMetadata(undefined);
    }
  }, [videoId]);

  return { thumbnail, metadata };
}
