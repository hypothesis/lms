/**
<<<<<<< HEAD
 * Replace parameters in a URL template with values from a `params` object and
 * returns the expanded URL.
 *
 *   replaceURLParams('/things/:id', {id: 'foo'}) => '/things/foo'
 *
 * @throws Error in case any provided param does not have a matching
 *               placeholder in the template URL
=======
 * Polyfill for `Object.hasOwn`.
 *
 * `hasOwn(someObject, property)` should be used instead of
 * `someObject.hasOwnProperty(name)`.
 */
function hasOwn(object: object, property: string): boolean {
  return Object.prototype.hasOwnProperty.call(object, property);
}

/**
 * Replace parameters in a URL template with values from a `params` object.
 *
 * Returns an object containing the expanded URL and a dictionary of unused
 * parameters.
 *
 *   replaceURLParams('/things/:id', {id: 'foo', q: 'bar'}) =>
 *     {url: '/things/foo', unusedParams: {q: 'bar'}}
>>>>>>> 04db3bbe8 (Add logic to dynamically build URLs from a template and params)
 */
export function replaceURLParams<Param>(
  urlTemplate: string,
  params: Record<string, Param>,
<<<<<<< HEAD
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
=======
): { url: string; unusedParams: Record<string, Param> } {
  const unusedParams: Record<string, Param> = {};
  for (const param in params) {
    if (hasOwn(params, param)) {
      const value = params[param];
      const urlParam = `:${param}`;
      if (urlTemplate.indexOf(urlParam) !== -1) {
        urlTemplate = urlTemplate.replace(
          urlParam,
          encodeURIComponent(String(value)),
        );
      } else {
        unusedParams[param] = value;
      }
    }
  }
  return { url: urlTemplate, unusedParams };
>>>>>>> 04db3bbe8 (Add logic to dynamically build URLs from a template and params)
}
