import { useMemo } from 'preact/hooks';
import type { LinkProps } from 'wouter-preact';
import { Link as RouterLink, useSearch } from 'wouter-preact';

import { urlWithOrgPublicId } from '../../utils/dashboard/hooks';

export default function DashboardLink({ href, to, ...rest }: LinkProps) {
  const query = useSearch();
  const enhancedHref = useMemo(
    () => urlWithOrgPublicId(href ?? to, query),
    [href, query, to],
  );
  return <RouterLink href={enhancedHref.toString()} {...rest} />;
}
