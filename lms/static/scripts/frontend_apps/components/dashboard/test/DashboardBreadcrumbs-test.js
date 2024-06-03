import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import DashboardBreadcrumbs from '../DashboardBreadcrumbs';

describe('DashboardBreadcrumbs', () => {
  function createComponent(props = {}) {
    return mount(<DashboardBreadcrumbs {...props} />);
  }

  [['foo', 'bar'], [], ['one', 'two', 'three']].forEach(links => {
    it('shows expected amount of links', () => {
      const wrapper = createComponent({
        links: links.map(title => ({ title, href: `/${title}` })),
      });

      // Breadcrumbs always renders a static extra link for the home page
      assert.equal(wrapper.find('BreadcrumbLink').length, links.length + 1);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () =>
        createComponent({
          links: [
            { title: 'Foo', href: '/foo' },
            { title: 'Bar', href: '/bar' },
          ],
        }),
    }),
  );
});
