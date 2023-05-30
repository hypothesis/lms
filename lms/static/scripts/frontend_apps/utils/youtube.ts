import type { YouTubeMetadata } from '../api-types';
import { isAPIError } from '../errors';
import { urlPath, useAPIFetch } from './api';

/**
 * Tries to resolve the video ID from a YouTube URL
 * @return null if the ID could not be resolved
 */
export function videoIdFromYouTubeURL(url: string): string | null {
  let parsedURL;
  try {
    parsedURL = new URL(url);
  } catch (e) {
    return null;
  }

  if (
    !parsedURL.protocol.match(/^https?:$/) ||
    !['www.youtube.com', 'youtube.com', 'youtu.be'].includes(parsedURL.host)
  ) {
    return null;
  }

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
  return match?.[2] ?? null;
}

type YouTubeVideoInfo = {
  isLoading: boolean;
  image?: string;
  title?: string;
  channel?: string;
  error?: 'video_not_found' | 'unknown';
};

/* istanbul ignore next */
export function useYouTubeVideoInfo(videoId: string | null): YouTubeVideoInfo {
  const metadata = useAPIFetch<YouTubeMetadata>(
    videoId ? urlPath`/api/youtube/videos/${videoId}` : null
  );

  if (metadata.error) {
    return {
      isLoading: metadata.isLoading,
      error:
        isAPIError(metadata.error) &&
        metadata.error.errorCode === 'youtube_video_not_found'
          ? 'video_not_found'
          : 'unknown',
    };
  }

  return {
    isLoading: metadata.isLoading,
    image: metadata.data?.image,
    title: metadata.data?.title,
    channel: metadata.data?.channel,
  };
}
