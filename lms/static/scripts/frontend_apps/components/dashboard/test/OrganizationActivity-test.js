import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import OrganizationActivity, { $imports } from '../OrganizationActivity';

describe('OrganizationActivity', () => {
  const courses = [
    {
      id: 1,
      title: 'Course A',
    },
    {
      id: 2,
      title: 'Course B',
    },
  ];

  let fakeUseAPIFetch;
  let fakeConfig;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().resolves(courses);
    fakeConfig = {
      dashboard: {
        routes: {
          organization_courses:
            '/api/dashboard/organizations/:organization_public_id',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        useAPIFetch: fakeUseAPIFetch,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <OrganizationActivity organizationPublicId="abc" />
      </Config.Provider>,
    );
  }

  it('sets loading state in table while data is loading', () => {
    fakeUseAPIFetch.returns({ isLoading: true });

    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.isTrue(tableElement.prop('loading'));
  });

  it('shows error if loading data fails', () => {
    fakeUseAPIFetch.returns({ error: new Error('Something failed') });

    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'Could not load courses');
  });

  it('shows empty courses message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No courses found');
  });

  courses.forEach(course => {
    it('renders course links', () => {
      const wrapper = createComponent();
      const item = wrapper
        .find('OrderableActivityTable')
        .props()
        .renderItem(course);
      const itemWrapper = mount(item);

      assert.equal(itemWrapper.text(), course.title);
      assert.equal(itemWrapper.prop('href'), `/courses/${course.id}`);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
