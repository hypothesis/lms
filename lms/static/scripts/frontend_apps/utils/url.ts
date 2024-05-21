/**
 * Replace parameters in a URL template with values from a `params` object and
 * returns the expanded URL.
 *
 *   replaceURLParams('/things/:id', {id: 'foo'}) => '/things/foo'
 *
 * @throws Error in case any provided param does not have a matching
 *               placeholder in the template URL
 */
export function replaceURLParams<Param>(
  urlTemplate: string,
  params: Record<string, Param>,
): string {
  const paramEntries = Object.entries(params);
  let url = urlTemplate;

  for (const [param, value] of paramEntries) {
    const urlParam = `:${param}`;
    if (!url.includes(urlParam)) {
      throw new Error(
        `Parameter "${param}" not found in "${urlTemplate}" URL template`,
      );
    }

    // Replace all occurrences of the same param in the template
    url = url.replaceAll(urlParam, encodeURIComponent(String(value)));
  }

  return url;
}
