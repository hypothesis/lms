import {
  ArrowLeftIcon,
  CaretRightIcon,
  Link,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

export type BreadcrumbLink = {
  title: string;
  href: string;
};

export type DashboardBreadcrumbsProps = {
  links?: BreadcrumbLink[];
};

function BreadcrumbLink({ title, href }: BreadcrumbLink) {
  return (
    <RouterLink href={href} asChild>
      <Link
        underline="always"
        variant="text-light"
        classes="truncate font-normal"
      >
        <ArrowLeftIcon className="inline-block md:hidden mr-1 align-sub" />
        {title}
      </Link>
    </RouterLink>
  );
}

/**
 * Navigation breadcrumbs showing a list of links
 */
export default function DashboardBreadcrumbs({
  links = [],
}: DashboardBreadcrumbsProps) {
  const linksWithHome = useMemo(
    (): BreadcrumbLink[] => [{ title: 'All courses', href: '' }, ...links],
    [links],
  );

  return (
    <div
      className="flex flex-row gap-0.5 w-full font-semibold"
      data-testid="breadcrumbs-container"
    >
      {linksWithHome.map(({ title, href }, index) => {
        const isLastLink = index === linksWithHome.length - 1;
        return (
          <span
            key={`${index}${href}`}
            className={classnames('gap-0.5', {
              // In mobile devices, show only the last link
              'md:flex hidden': !isLastLink,
              'flex max-w-full': isLastLink,
              // Distribute max width for every link as evenly as possible.
              // These must be static values for Tailwind to detect them.
              // See https://tailwindcss.com/docs/content-configuration#dynamic-class-names
              'md:max-w-[50%]': linksWithHome.length === 2,
              'md:max-w-[33%]': linksWithHome.length === 3,
              'md:max-w-[25%]': linksWithHome.length === 4,
              'md:max-w-[230px]': linksWithHome.length > 4,
            })}
          >
            <BreadcrumbLink href={href} title={title} />
            {!isLastLink && (
              <CaretRightIcon className="text-color-text-light" />
            )}
          </span>
        );
      })}
    </div>
  );
}
