import type { LinkProps } from '@hypothesis/frontend-shared';
import { Link } from '@hypothesis/frontend-shared';

function FooterLink(
  props: Omit<LinkProps, 'underline' | 'variant' | 'target' | 'rel'>,
) {
  return (
    <Link
      {...props}
      underline="hover"
      variant="custom"
      target="_blank"
      // The Link component sets rel="noopener noreferrer", but since we are
      // linking to known pages, we want to remove noreferrer
      rel="noopener"
    />
  );
}

export default function DashboardFooter() {
  return (
    <footer className="w-full bg-grey-9 text-white p-3">
      <div className="mx-auto max-w-6xl flex justify-between items-center">
        <div className="flex gap-3">
          <FooterLink href="https://web.hypothes.is" classes="font-bold">
            <img
              alt="Hypothesis logo"
              src="/static/images/hypothesis-logo.svg"
              className="mr-2 inline"
            />
            hypothes.is
          </FooterLink>
        </div>
        <div className="flex gap-3">
          <FooterLink href="https://web.hypothes.is/help/">Help</FooterLink>
          <FooterLink href="https://web.hypothes.is/contact/">
            Contact
          </FooterLink>
          <FooterLink href="https://web.hypothes.is/terms-of-service/">
            Terms of Service
          </FooterLink>
          <FooterLink href="https://web.hypothes.is/privacy/">
            Privacy Policy
          </FooterLink>
        </div>
      </div>
    </footer>
  );
}
