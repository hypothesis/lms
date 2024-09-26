import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';
import sinon from 'sinon';

import { Config } from '../../../config';
import { APIError } from '../../../errors';
import SyncGradesButton, { $imports } from '../SyncGradesButton';

describe('SyncGradesButton', () => {
  let fakeConfig;
  let fakeApiCall;
  let fakeUsePolledAPIFetch;
  let fakeOnSyncScheduled;
  let shouldRefreshCallback;

  const studentsToSync = [
    { h_userid: '123', grade: 0.5 },
    { h_userid: '456', grade: 0.2 },
  ];

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves(undefined);
    fakeUsePolledAPIFetch = sinon.stub().callsFake(({ shouldRefresh }) => {
      // "Collect" shouldRefresh callback so that we can test its behavior
      // individually
      shouldRefreshCallback = shouldRefresh;

      return {
        data: null,
        isLoading: true,
      };
    });
    fakeOnSyncScheduled = sinon.stub();

    fakeConfig = {
      dashboard: {
        routes: {
          assignment_grades_sync: '/api/assignments/:assignment_id/grades/sync',
        },
      },
      api: { authToken: 'authToken' },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        apiCall: fakeApiCall,
        usePolledAPIFetch: fakeUsePolledAPIFetch,
      },
      'wouter-preact': {
        useParams: sinon.stub().returns({ assignmentId: '123' }),
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent(studentsToSync) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <SyncGradesButton
          studentsToSync={studentsToSync}
          onSyncScheduled={fakeOnSyncScheduled}
        />
      </Config.Provider>,
    );
  }

  function buttonText(wrapper) {
    return wrapper.find('Button').text();
  }

  function isButtonDisabled(wrapper) {
    return wrapper.find('Button').prop('disabled');
  }

  [
    {
      fetchResult: { data: null },
      expectedResult: false,
    },
    {
      fetchResult: {
        data: { status: 'scheduled' },
      },
      expectedResult: true,
    },
    {
      fetchResult: {
        data: { status: 'in_progress' },
      },
      expectedResult: true,
    },
    {
      fetchResult: {
        data: { status: 'finished' },
      },
      expectedResult: false,
    },
  ].forEach(({ fetchResult, expectedResult }) => {
    it('shouldRefresh callback behaves as expected', () => {
      createComponent();
      assert.equal(shouldRefreshCallback(fetchResult), expectedResult);
    });
  });

  [undefined, studentsToSync].forEach(studentsToSync => {
    it('shows loading text when getting initial data', () => {
      const wrapper = createComponent(studentsToSync);

      assert.equal(buttonText(wrapper), 'Loading...');
      assert.isTrue(isButtonDisabled(wrapper));
    });
  });

  ['scheduled', 'in_progress'].forEach(status => {
    it('shows syncing text when grades are being synced', () => {
      fakeUsePolledAPIFetch.returns({
        isLoading: false,
        data: { status },
      });

      const wrapper = createComponent(studentsToSync);

      assert.equal(buttonText(wrapper), 'Syncing grades');
      assert.isTrue(isButtonDisabled(wrapper));
    });
  });

  it('shows syncing errors and allows to retry', () => {
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      data: { status: 'failed' },
    });

    const wrapper = createComponent(studentsToSync);

    assert.equal(buttonText(wrapper), 'Error syncing. Click to retry');
    assert.isFalse(isButtonDisabled(wrapper));
  });

  it('shows error when checking current sync status', () => {
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      error: new Error(''),
    });

    const wrapper = createComponent(studentsToSync);

    assert.equal(buttonText(wrapper), 'Error checking sync status');
    assert.isFalse(isButtonDisabled(wrapper));
  });

  [
    { students: studentsToSync, expectedAmount: studentsToSync.length },
    {
      students: [...studentsToSync, ...studentsToSync],
      expectedAmount: studentsToSync.length * 2,
    },
  ].forEach(({ students, expectedAmount }) => {
    it('shows the amount of students to be synced when current status is "finished"', () => {
      fakeUsePolledAPIFetch.returns({
        isLoading: false,
        data: { status: 'finished' },
      });

      const wrapper = createComponent(students);

      assert.equal(buttonText(wrapper), `Sync ${expectedAmount} grades`);
      assert.isFalse(isButtonDisabled(wrapper));
    });
  });

  it('shows the amount of students to be synced when a previous sync has not happened at all', () => {
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      error: new APIError(404, {}),
    });

    const wrapper = createComponent(studentsToSync);

    assert.equal(buttonText(wrapper), `Sync ${studentsToSync.length} grades`);
    assert.isFalse(isButtonDisabled(wrapper));
  });

  it('shows grades synced when no students need to be synced', () => {
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      data: { status: 'finished' },
    });

    const wrapper = createComponent([]);

    assert.equal(buttonText(wrapper), 'Grades synced');
    assert.isTrue(isButtonDisabled(wrapper));
  });

  it('submits grades when the button is clicked, then triggers sync status polling', async () => {
    const mutate = sinon.stub();
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      data: { status: 'finished' },
      mutate,
    });

    const wrapper = createComponent(studentsToSync);
    await act(() => wrapper.find('Button').props().onClick());

    assert.calledWith(mutate, { status: 'scheduled' });
    assert.called(fakeApiCall);
    assert.deepEqual(
      {
        grades: [
          { h_userid: '123', grade: 0.5 },
          { h_userid: '456', grade: 0.2 },
        ],
      },
      fakeApiCall.lastCall.args[0].data,
    );
    assert.called(fakeOnSyncScheduled);
  });

  it('sets status to error when scheduling a sync fails', async () => {
    const mutate = sinon.stub();
    fakeUsePolledAPIFetch.returns({
      isLoading: false,
      data: { status: 'finished' },
      mutate,
    });
    fakeApiCall.rejects(new Error('Error scheduling'));

    const wrapper = createComponent(studentsToSync);
    await act(() => wrapper.find('Button').props().onClick());

    assert.calledWith(mutate, { status: 'failed' });
    assert.notCalled(fakeOnSyncScheduled);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
