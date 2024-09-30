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
  let fakeOnSyncScheduled;

  const studentsToSync = [
    { h_userid: '123', grade: 0.5 },
    { h_userid: '456', grade: 0.2 },
  ];

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves(undefined);
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
      },
      'wouter-preact': {
        useParams: sinon.stub().returns({ assignmentId: '123' }),
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent(
    studentsToSync,
    lastSync = {
      data: null,
      isLoading: true,
    },
  ) {
    return mount(
      <Config.Provider value={fakeConfig}>
        <SyncGradesButton
          studentsToSync={studentsToSync}
          lastSync={lastSync}
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

  [undefined, studentsToSync].forEach(studentsToSync => {
    it('shows loading text when getting initial data', () => {
      const wrapper = createComponent(studentsToSync);

      assert.equal(buttonText(wrapper), 'Loading...');
      assert.isTrue(isButtonDisabled(wrapper));
    });
  });

  ['scheduled', 'in_progress'].forEach(status => {
    it('shows syncing text when grades are being synced', () => {
      const wrapper = createComponent(studentsToSync, {
        isLoading: false,
        data: { status },
      });

      assert.equal(buttonText(wrapper), 'Syncing grades');
      assert.isTrue(isButtonDisabled(wrapper));
    });
  });

  it('shows syncing errors and allows to retry', () => {
    const wrapper = createComponent(studentsToSync, {
      isLoading: false,
      data: { status: 'failed' },
    });

    assert.equal(buttonText(wrapper), 'Error syncing. Click to retry');
    assert.isFalse(isButtonDisabled(wrapper));
  });

  it('shows error when checking current sync status', () => {
    const wrapper = createComponent(studentsToSync, {
      isLoading: false,
      error: new Error(''),
    });

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
      const wrapper = createComponent(students, {
        isLoading: false,
        data: { status: 'finished' },
      });

      assert.equal(buttonText(wrapper), `Sync ${expectedAmount} grades`);
      assert.isFalse(isButtonDisabled(wrapper));
    });
  });

  it('shows the amount of students to be synced when a previous sync has not happened at all', () => {
    const wrapper = createComponent(studentsToSync, {
      isLoading: false,
      error: new APIError(404, {}),
    });

    assert.equal(buttonText(wrapper), `Sync ${studentsToSync.length} grades`);
    assert.isFalse(isButtonDisabled(wrapper));
  });

  it('shows grades synced when no students need to be synced', () => {
    const wrapper = createComponent([], {
      isLoading: false,
      data: { status: 'finished' },
    });

    assert.equal(buttonText(wrapper), 'Grades synced');
    assert.isTrue(isButtonDisabled(wrapper));
  });

  it('submits grades when the button is clicked, then calls onSyncScheduled', async () => {
    const wrapper = createComponent(studentsToSync, {
      isLoading: false,
      data: { status: 'finished' },
      mutate: sinon.stub(),
    });
    await act(() => wrapper.find('Button').props().onClick());

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
    fakeApiCall.rejects(new Error('Error scheduling'));

    const mutate = sinon.stub();
    const wrapper = createComponent(studentsToSync, {
      isLoading: false,
      data: { status: 'finished' },
      mutate,
    });
    await act(() => wrapper.find('Button').props().onClick());

    assert.calledWith(mutate.lastCall, sinon.match({ status: 'failed' }));
    assert.notCalled(fakeOnSyncScheduled);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
