import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import DashboardApp, { $imports } from '../DashboardApp';

describe('DashboardApp', () => {
  let fakeUseAPIFetch;
  let fakeConfig;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().returns({ data: [], isLoading: false });
    fakeConfig = {
      dashboard: {
        assignment: {
          title: 'The assignment',
        },
        assignmentStatsApi: {
          path: '/api/assignment/123/stats',
        },
      },
      api: { authToken: 'authToken' },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': { useAPIFetch: fakeUseAPIFetch },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <DashboardApp />
      </Config.Provider>,
    );
  }

  it('loads assignment stats on mount, via API call', () => {
    assert.notCalled(fakeUseAPIFetch);
    createComponent();
    assert.calledWith(fakeUseAPIFetch, '/api/assignment/123/stats');
  });

  it('passes assignment info down to StudentsActivity', () => {
    const wrapper = createComponent();
    const table = wrapper.find('StudentsActivity');

    assert.deepEqual(table.prop('assignment'), {
      title: 'The assignment',
    });
  });

  context('when loading students', () => {
    [true, false].forEach(isLoading => {
      it('passes loading state down to StudentsActivity', () => {
        fakeUseAPIFetch.returns({ isLoading });
        const wrapper = createComponent();

        assert.equal(
          wrapper.find('StudentsActivity').prop('loading'),
          isLoading,
        );
      });
    });

    [undefined, [1, 2, 3]].forEach(students => {
      it('passes list of students down to StudentsActivity', () => {
        fakeUseAPIFetch.returns({ isLoading: false, data: students });
        const wrapper = createComponent();

        assert.deepEqual(
          wrapper.find('StudentsActivity').prop('students'),
          students ?? [],
        );
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
