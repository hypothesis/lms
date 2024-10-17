/**
 * Tries to resolve the video ID from a YouTube URL
 * @return null if the ID could not be resolved
 */
export function videoIdFromYouTubeURL(url: string): string | null {
  let parsedURL;
  try {
    parsedURL = new URL(url);
  } catch {
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
    /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|live\/|watch\?v=|&v=)([^#&?]*).*/,
  );
  return match?.[2] ?? null;
}

export function isYouTubeURL(url: string): boolean {
  return videoIdFromYouTubeURL(url) !== null;
}
