import {
  checkAccessibility,
  mockImportedComponents,
  waitFor,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { ClientRPC, Services } from '../../services';
import GradingControls, { $imports } from '../GradingControls';

describe('GradingControls', () => {
  let fakeApiCall;
  let fakeConfig;
  let fakeStudents;
  let fakeClientRPC;
  let fakeConfirm;

  /**
   * Helper to return a list of displayNames of the students.
   *
   * @param {import("enzyme").CommonWrapper} wrapper - Enzyme wrapper
   * @returns {Array<string>}
   */
  function getDisplayNames(wrapper) {
    return wrapper
      .find('StudentSelector')
      .prop('students')
      .map(s => {
        return s.displayName;
      });
  }

  beforeEach(() => {
    fakeApiCall = sinon.stub();
    fakeConfig = {
      api: {
        authToken: 'dummyAuthToken',
      },
    };
    fakeStudents = [
      {
        userid: 'acct:student1@authority',
        displayName: 'Student 1',
        LISResultSourcedId: 1,
        LISOutcomeServiceUrl: '',
        lmsId: '123',
      },
      {
        userid: 'acct:student2@authority',
        displayName: 'Student 2',
        LISResultSourcedId: 2,
        LISOutcomeServiceUrl: '',
        lmsId: '456',
      },
    ];

    fakeClientRPC = {
      setFocusedUser: sinon.stub(),
    };

    fakeConfirm = sinon.stub().resolves(false);

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '@hypothesis/frontend-shared': { confirm: fakeConfirm },
      '../utils/api': {
        apiCall: fakeApiCall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const selectFirstStudent = wrapper =>
    act(() =>
      wrapper.find('StudentSelector').props().onSelectStudent(fakeStudents[0]),
    );

  const renderGrader = (props = {}) => {
    const services = new Map([[ClientRPC, fakeClientRPC]]);
    return mount(
      <Config.Provider value={fakeConfig}>
        <Services.Provider value={services}>
          <GradingControls
            students={fakeStudents}
            clientRPC={fakeClientRPC}
            {...props}
          />
        </Services.Provider>
      </Config.Provider>,
    );
  };

  it('orders the students by displayName', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Student Beta',
      },
      {
        displayName: 'Students Beta',
      },
      {
        displayName: 'Beta',
      },
      {
        displayName: 'student Beta',
      },
      {
        displayName: 'Student Delta',
      },
      {
        displayName: 'Student Alpha',
      },
      {
        displayName: 'Alpha',
      },
    ];
    const wrapper = renderGrader();
    const orderedStudentNames = getDisplayNames(wrapper);
    assert.match(
      [
        'Alpha',
        'Beta',
        'Student Alpha',
        'Student Beta',
        // 'student Beta' ties with 'Student Beta',
        // but since 'Student Beta' came first, it wins.
        'student Beta',
        'Student Delta',
        'Students Beta',
      ],
      orderedStudentNames,
    );
  });

  it('puts students with empty displayNames at the beginning of sorted students', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Student Beta',
      },
      {
        displayName: '',
      },
    ];
    const wrapper = renderGrader();
    const orderedStudentNames = wrapper
      .find('StudentSelector')
      .prop('students')
      .map(s => {
        return s.displayName;
      });
    assert.match(['', 'Student Beta'], orderedStudentNames);
  });

  it('does not set a focus user by default', () => {
    renderGrader();
    assert.calledWith(fakeClientRPC.setFocusedUser, null);
  });

  it('sets the focused user when a valid student is selected', async () => {
    const wrapper = renderGrader();

    await selectFirstStudent(wrapper);

    assert.calledWith(
      fakeClientRPC.setFocusedUser,
      fakeStudents[0],
      null /* groups */,
    );
    assert.notCalled(fakeApiCall);
  });

  describe("Syncing focused user's groups when setting focused user", () => {
    let studentGroups;

    beforeEach(() => {
      sinon.stub(console, 'error');
      fakeConfig.api.sync = {
        path: '/fake/path',
        data: { foo: 'bar' },
      };
      studentGroups = [{ groupid: 'group1' }, { groupid: 'group2' }];
      fakeApiCall.resolves(studentGroups);
    });

    afterEach(() => {
      console.error.restore();
    });

    it("fetches the focused user's groups from the sync API", async () => {
      const wrapper = renderGrader();

      // Initial call on first render sets focused user to null
      assert.calledOnce(fakeClientRPC.setFocusedUser);

      selectFirstStudent(wrapper);

      await waitFor(() => fakeApiCall.called);

      assert.calledWith(
        fakeApiCall,
        sinon.match({
          authToken: 'dummyAuthToken',
          path: '/fake/path',
          data: { foo: 'bar', gradingStudentId: '123' },
        }),
      );
      assert.notCalled(console.error);
    });

    it('passes fetched student groups to RPC method', async () => {
      const wrapper = renderGrader();

      selectFirstStudent(wrapper);

      await waitFor(() => fakeApiCall.called);

      // Second call to set a "real" focused user
      assert.equal(fakeClientRPC.setFocusedUser.callCount, 2);
      assert.calledWith(
        fakeClientRPC.setFocusedUser,
        fakeStudents[0],
        studentGroups,
      );
    });

    it('logs an error to the console if fetching from sync API fails', async () => {
      fakeApiCall.rejects();
      const wrapper = renderGrader();

      selectFirstStudent(wrapper);

      await waitFor(() => fakeApiCall.called);

      assert.calledOnce(console.error);
      assert.calledWith(
        console.error,
        'Unable to fetch student groups from sync API',
      );
      // Still set the focused user, but don't pass any groups
      assert.calledWith(
        fakeClientRPC.setFocusedUser,
        fakeStudents[0],
        /* groups */ null,
      );
    });
  });

  it('clears the focused user if no student is selected', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find('StudentSelector').props().onSelectStudent(null);
    });

    assert.calledWith(
      fakeClientRPC.setFocusedUser,
      null /* user */,
      null /* groups */,
    );
  });

  context('when has unsaved grade changes', () => {
    const setUnsavedChanges = wrapper =>
      act(() => wrapper.find('SubmitGradeForm').props().onUnsavedChanges(true));
    const getSelectedStudent = wrapper =>
      wrapper.find('StudentSelector').props().selectedStudent;
    const selectStudent = (wrapper, student) =>
      act(() =>
        wrapper.find('StudentSelector').props().onSelectStudent(student),
      );

    [
      // Selected student should still be the first
      {
        discardChanges: false,
        expectedStudentAfterChange: () => fakeStudents[0],
      },

      // Selected student should change from first to second
      {
        discardChanges: true,
        expectedStudentAfterChange: () => fakeStudents[1],
      },
    ].forEach(({ discardChanges, expectedStudentAfterChange }) => {
      it('"cancels" selected user change if instructor selected to continue editing', async () => {
        const wrapper = renderGrader();
        await selectFirstStudent(wrapper);

        await setUnsavedChanges(wrapper);
        wrapper.update();
        fakeConfirm.resolves(discardChanges);

        // Try to select another student
        await selectStudent(wrapper, fakeStudents[1]);
        wrapper.update();

        assert.equal(getSelectedStudent(wrapper), expectedStudentAfterChange());
      });
    });

    it('resets unsaved changes when student is changed and changes are discarded', async () => {
      const wrapper = renderGrader();
      await selectFirstStudent(wrapper);

      await setUnsavedChanges(wrapper);
      wrapper.update();
      fakeConfirm.resolves(true);

      // Try to select another student
      await selectStudent(wrapper, fakeStudents[1]);
      wrapper.update();

      assert.calledOnce(fakeConfirm);

      // Select first student again
      await selectFirstStudent(wrapper);
      wrapper.update();

      // It should not have called confirm for a second time
      assert.calledOnce(fakeConfirm);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderGrader(),
    }),
  );
});
