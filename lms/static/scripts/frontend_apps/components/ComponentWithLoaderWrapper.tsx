import { Card, CardContent } from '@hypothesis/frontend-shared';
import type { ComponentChildren, FunctionalComponent } from 'preact';
import { useEffect, useMemo, useState } from 'preact/hooks';
import type { Parser } from 'wouter-preact';
import { useLocation, useParams, useRouter } from 'wouter-preact';

import type { ConfigObject, Ensure } from '../config';
import { useConfig } from '../config';
import type { ErrorLike } from '../errors';
import ErrorDisplay from './ErrorDisplay';
import AssignmentActivity, {
  loader as assignmentLoader,
} from './dashboard/AssignmentActivity';
import CourseActivity, {
  loader as courseLoader,
} from './dashboard/CourseActivity';
import OrganizationActivity, {
  loader as organizationLoader,
} from './dashboard/OrganizationActivity';

export type LoaderOptions = {
  config: Ensure<ConfigObject, 'dashboard' | 'api'>;
  params: Record<string, string>;
  signal: AbortSignal;
};

type RouteModule = {
  loader: (opts: LoaderOptions) => Promise<unknown>;
  Component: FunctionalComponent;
};

const matchRoute = (parser: Parser, route: string, path: string) => {
  const { pattern, keys } = parser(route);

  // array destructuring loses keys, so this is done in two steps
  const result = pattern.exec(path) || [];

  // when parser is in "loose" mode, `$base` is equal to the
  // first part of the route that matches the pattern
  // (e.g. for pattern `/a/:b` and path `/a/1/2/3` the `$base` is `a/1`)
  // we use this for route nesting
  const [$base, ...matches] = result;

  if ($base === undefined) {
    return [false, null];
  }

  // an object with parameters matched, e.g. { foo: "bar" } for "/:foo"
  // we "zip" two arrays here to construct the object
  // ["foo"], ["bar"] → { foo: "bar" }
  const groups = Object.fromEntries(keys.map((key, i) => [key, matches[i]]));

  // convert the array to an instance of object
  // this makes it easier to integrate with the existing param implementation
  const obj = { ...matches };
  // merge named capture groups with matches array
  Object.assign(obj, groups);

  return [true, obj];
};

function useRouteModule(routeToModuleMap: Map<string, () => RouteModule>) {
  const { parser } = useRouter();
  const [location] = useLocation();

  return useMemo(() => {
    for (const [route, moduleResolver] of routeToModuleMap) {
      const [matches, params] = matchRoute(parser, route, location);
      if (matches) {
        return { module: moduleResolver(), params: params ?? {} };
      }
    }

    return undefined;
  }, [location, parser, routeToModuleMap]);
}

const routesMap = new Map<string, () => RouteModule>([
  [
    '/assignments/:assignmentId',
    () =>
      ({
        loader: assignmentLoader,
        Component: AssignmentActivity,
      }) as RouteModule,
  ],
  [
    '/courses/:courseId',
    () =>
      ({
        loader: courseLoader,
        Component: CourseActivity,
      }) as RouteModule,
  ],
  [
    '',
    () =>
      ({
        loader: organizationLoader,
        Component: OrganizationActivity,
      }) as RouteModule,
  ],
]);

export default function ComponentWithLoaderWrapper() {
  const config = useConfig(['dashboard', 'api']);
  const [component, setComponent] = useState<ComponentChildren>();
  const [loading, setLoading] = useState(true);
  const [fatalError, setFatalError] = useState<ErrorLike>();
  const { organizationId } = useParams<{ organizationId: string }>();
  const routeModule = useRouteModule(routesMap);

  useEffect(() => {
    if (!routeModule) {
      return () => {};
    }

    const abortController = new AbortController();
    const { module, params } = routeModule;
    const { loader, Component } = module;

    setLoading(true);
    loader({
      config,
      params: { ...params, organizationId },
      signal: abortController.signal,
    })
      .then(loaderResult =>
        setComponent(<Component loaderResult={loaderResult} />),
      )
      .catch(e => setFatalError(e))
      .finally(() => setLoading(false));

    return () => abortController.abort();
  }, [config, organizationId, routeModule]);

  if (fatalError) {
    return (
      <Card>
        <CardContent>
          <ErrorDisplay error={fatalError} />
        </CardContent>
      </Card>
    );
  }

  return !component ? (
    <div className="text-center">Initial loading...</div>
  ) : (
    <>
      {loading && <div className="text-center">Transitioning...</div>}
      {component}
    </>
  );
}
