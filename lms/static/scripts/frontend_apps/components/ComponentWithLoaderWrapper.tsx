import { Card, CardContent } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { useParams, useRoute } from 'wouter-preact';

import type { ConfigObject, Ensure } from '../config';
import { useConfig } from '../config';
import type { ErrorLike } from '../errors';
import ErrorDisplay from './ErrorDisplay';

export type LoaderOptions = {
  config: Ensure<ConfigObject, 'dashboard' | 'api'>;
  params: Record<string, string>;
  signal: AbortSignal;
};

export default function ComponentWithLoaderWrapper() {
  const config = useConfig(['dashboard', 'api']);
  const [component, setComponent] = useState<ComponentChildren>();
  const [loading, setLoading] = useState(true);
  const [fatalError, setFatalError] = useState<ErrorLike>();

  const [isAssignment, assignmentParams] = useRoute(
    '/assignments/:assignmentId',
  );
  const [isCourse, courseParams] = useRoute('/courses/:courseId');
  const [isHome] = useRoute('');
  const globalParams = useParams();
  const assignmentId = assignmentParams?.assignmentId ?? '';
  const courseId = courseParams?.courseId ?? '';
  const organizationId = globalParams.organizationId ?? '';

  useEffect(() => {
    const loaderModule = isAssignment
      ? import('./dashboard/AssignmentActivity')
      : isCourse
        ? import('./dashboard/CourseActivity')
        : import('./dashboard/OrganizationActivity');
    const params = { assignmentId, courseId, organizationId };

    const abortController = new AbortController();
    loaderModule.then(async ({ loader, default: Component }) => {
      setLoading(true);
      try {
        const loaderResult = await loader({
          config,
          params,
          signal: abortController.signal,
        });
        setComponent(<Component loaderResult={loaderResult} params={params} />);
      } catch (e) {
        setFatalError(e);
      } finally {
        setLoading(false);
      }
    });

    return () => abortController.abort();
  }, [assignmentId, courseId, organizationId, config, isAssignment, isCourse]);

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
