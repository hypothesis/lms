import {
  ArrowLeftIcon,
  CaretRightIcon,
  Link,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { Link as RouterLink } from 'wouter-preact';

export type BreadcrumbLink = {
  title: string;
  href: string;
};

export type DashboardBreadcrumbsProps = {
  links: BreadcrumbLink[];
};

function BreadcrumbLink({ title, href }: BreadcrumbLink) {
  return (
    <RouterLink href={href} asChild>
      <Link underline="hover" variant="text-light" classes="truncate">
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
  links,
}: DashboardBreadcrumbsProps) {
  return (
    <div
      className="flex flex-row gap-0.5 w-full font-semibold"
      data-testid="breadcrumbs-container"
    >
      {links.map(({ title, href }, index) => {
        const isLastLink = index === links.length - 1;
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
              'md:max-w-[50%]': links.length === 2,
              'md:max-w-[33.333333%]': links.length === 3,
              'md:max-w-[25%]': links.length === 4,
              'md:max-w-[230px]': links.length > 4,
            })}
          >
            <BreadcrumbLink href={href} title={title} />
            {!isLastLink && <CaretRightIcon />}
          </span>
        );
      })}
    </div>
  );
}
