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

/**
 * Converts a record into a URLSearchParams object.
 * Any param which is an array will be appended for every one of its values.
 */
export function recordToSearchParams(
  params: Record<string, string | string[]>,
): URLSearchParams {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([name, value]) => {
    if (Array.isArray(value)) {
      value.forEach(v => queryParams.append(name, v));
    } else {
      queryParams.append(name, value);
    }
  });

  return queryParams;
}
