import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import DashboardApp, { $imports } from '../DashboardApp';

describe('DashboardApp', () => {
  let fakeApiCall;
  let fakeConfig;
  let fakeUseParams;

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves([]);
    fakeUseParams = sinon.stub().returns({ assignmentId: '123' });
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
      'wouter-preact': { useParams: fakeUseParams },
      '../../utils/api': { apiCall: fakeApiCall },
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
    assert.notCalled(fakeApiCall);
    createComponent();
    assert.calledWith(fakeApiCall, {
      authToken: 'authToken',
      method: 'GET',
      path: '/api/assignment/123/stats',
    });
  });

  it('passes assignment info down to StudentsActivityTable', () => {
    const wrapper = createComponent();
    const table = wrapper.find('StudentsActivityTable');

    assert.deepEqual(table.prop('assignment'), {
      title: 'The assignment',
      id: '123',
    });
  });

  context('when loading students', () => {
    const configureApiCall = () => {
      let resolve;
      const promise = new Promise(r => {
        resolve = r;
      });
      fakeApiCall.returns(promise);

      return async (wrapper, studentsList = []) => {
        resolve(studentsList);
        await promise;
        wrapper.update();
      };
    };

    it('passes loading state down to StudentsActivityTable', async () => {
      const resolveApiCall = configureApiCall();
      const wrapper = createComponent();

      // Loading is initially true
      assert.isTrue(wrapper.find('StudentsActivityTable').prop('loading'));

      // Once the API call promise resolves, it transitions to "not loading"
      await resolveApiCall(wrapper);
      assert.isFalse(wrapper.find('StudentsActivityTable').prop('loading'));
    });

    it('passes list of students down to StudentsActivityTable', async () => {
      const resolveApiCall = configureApiCall();
      const wrapper = createComponent();

      // Students is an empty list initially
      assert.deepEqual(
        wrapper.find('StudentsActivityTable').prop('students'),
        [],
      );

      // Once the API call promise resolves, it passes actual data
      await resolveApiCall(wrapper, [1, 2, 3]);
      assert.deepEqual(
        wrapper.find('StudentsActivityTable').prop('students'),
        [1, 2, 3],
      );
    });
  });
});
