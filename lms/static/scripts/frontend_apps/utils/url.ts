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

export type QueryParams = Record<string, string | string[] | undefined>;

/**
 * Converts a record into a URLSearchParams object.
 * Any param which is an array will be appended for every one of its values.
 */
export function recordToSearchParams(params: QueryParams): URLSearchParams {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([name, value]) => {
    // Skip params if their value is undefined
    if (value === undefined) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(v => queryParams.append(name, v));
    } else {
      queryParams.append(name, value);
    }
  });

  return queryParams;
}

/**
 * Converts a record into a query string.
 * The result is prefixed with a question mark (`?`) if it's not empty.
 *
 * Examples:
 *    {} -> ''
 *    { foo: [] } -> ''
 *    { foo: 'bar' } -> '?foo=bar'
 *    { foo: 'bar', something: ['hello', 'world'] } -> '?foo=bar&something=hello&something=world'
 */
export function recordToQueryString(params: QueryParams): string {
  const queryString = recordToSearchParams(params).toString();
  return queryString.length > 0 ? `?${queryString}` : '';
}

/**
 * Converts provided query string into a record.
 * Parameters that appear more than once will be converted to an array.
 */
export function queryStringToRecord(
  queryString: string,
): Record<string, string | string[]> {
  const queryParams = new URLSearchParams(queryString);
  const params: Record<string, string | string[]> = {};

  queryParams.forEach((value, name) => {
    if (!params[name]) {
      params[name] = value;
    } else if (Array.isArray(params[name])) {
      (params[name] as string[]).push(value);
    } else {
      params[name] = [params[name] as string, value];
    }
  });

  return params;
}
