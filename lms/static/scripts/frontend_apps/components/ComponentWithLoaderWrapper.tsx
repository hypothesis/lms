import type { ComponentChildren, FunctionComponent } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { useParams, useRoute } from 'wouter-preact';

import type { ConfigObject } from '../config';
import { useConfig } from '../config';

export type ComponentWithLoaderWrapperProps = {
  loaderModule: Promise<{
    loader: (options: {
      config: ConfigObject;
      params: Record<string, string | undefined>;
    }) => Promise<unknown>;
    default: FunctionComponent<{ loadResult: unknown }>;
  }>;
};

export default function ComponentWithLoaderWrapper() {
  const config = useConfig();
  const params = useParams();
  const [component, setComponent] = useState<ComponentChildren>();
  const [loading, setLoading] = useState(true);
  const [isAssignment] = useRoute('/assignments/:assignmentId');
  const [isCourse] = useRoute('/courses/:courseId');
  const [isHome] = useRoute('');

  useEffect(() => {
    const loaderModule = isAssignment
      ? import('./dashboard/AssignmentActivity')
      : isCourse
        ? import('./dashboard/CourseActivity')
        : import('./dashboard/OrganizationActivity');
    loaderModule.then(async ({ loader, default: Component }) => {
      // TODO Error handling
      setLoading(true);
      const loadResult = await loader({ config, params });
      setLoading(false);
      setComponent(<Component loadResult={loadResult} />);
    });
  }, [config, isAssignment, isCourse, params]);

  return !component ? (
    <>Initial loading...</>
  ) : (
    <>
      {loading && <>Transitioning...</>}
      {component}
    </>
  );
}
