import { act } from 'preact/test-utils';

import { mount } from 'enzyme';

import { Config } from '../../config';
import LMSGrader, { $imports } from '../LMSGrader';
import { checkAccessibility } from '../../../test-util/accessibility';
import { waitFor } from '../../../test-util/wait';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('LMSGrader', () => {
  let fakeApiCall;
  let fakeConfig;
  let fakeStudents;
  let fakeOnChange;
  let fakeClientRPC;

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
    fakeOnChange = sinon.spy();
    fakeClientRPC = {
      setFocusedUser: sinon.stub(),
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/api': {
        apiCall: fakeApiCall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderGrader = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <LMSGrader
          onChangeSelectedUser={fakeOnChange}
          students={fakeStudents}
          courseName={'course name'}
          assignmentName={'course assignment'}
          clientRPC={fakeClientRPC}
          {...props}
        >
          <div title="The assignment content iframe" />
        </LMSGrader>
      </Config.Provider>
    );
  };

  it('sets the assignment and course names', () => {
    const wrapper = renderGrader();
    assert.equal(
      wrapper.find('[data-testid="assignment-name"]').text(),
      'course assignment'
    );
    assert.equal(
      wrapper.find('[data-testid="course-name"]').text(),
      'course name'
    );
  });

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
      orderedStudentNames
    );
  });

  it('puts students with empty displayNames at the beginning of sorted students', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Student Beta',
      },
      {
        displayName: undefined,
      },
    ];
    const wrapper = renderGrader();
    const orderedStudentNames = wrapper
      .find('StudentSelector')
      .prop('students')
      .map(s => {
        return s.displayName;
      });
    assert.match([undefined, 'Student Beta'], orderedStudentNames);
  });

  it('does not set a focus user by default', () => {
    renderGrader();
    assert.calledWith(fakeClientRPC.setFocusedUser, null);
  });

  it('sets the focused user when a valid index is passed', () => {
    const wrapper = renderGrader();

    act(() => {
      wrapper.find('StudentSelector').props().onSelectStudent(0); // note: initial index is -1
    });

    assert.calledWith(
      fakeClientRPC.setFocusedUser,
      fakeStudents[0],
      null /* groups */
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

      act(() => {
        wrapper.find('StudentSelector').props().onSelectStudent(0);
      });

      await waitFor(() => fakeApiCall.called);

      assert.calledWith(
        fakeApiCall,
        sinon.match({
          authToken: 'dummyAuthToken',
          path: '/fake/path',
          data: { foo: 'bar', gradingStudentId: '123' },
        })
      );
      assert.notCalled(console.error);
    });

    it('Passes fetched student groups to RPC method', async () => {
      const wrapper = renderGrader();

      act(() => {
        wrapper.find('StudentSelector').props().onSelectStudent(0);
      });

      await waitFor(() => fakeApiCall.called);

      // Second call to set a "real" focused user
      assert.equal(fakeClientRPC.setFocusedUser.callCount, 2);
      assert.calledWith(
        fakeClientRPC.setFocusedUser,
        fakeStudents[0],
        studentGroups
      );
    });

    it('logs an error to the console if fetching from sync API fails', async () => {
      fakeApiCall.rejects();
      const wrapper = renderGrader();

      act(() => {
        wrapper.find('StudentSelector').props().onSelectStudent(0);
      });

      await waitFor(() => fakeApiCall.called);

      assert.calledOnce(console.error);
      assert.calledWith(
        console.error,
        'Unable to fetch student groups from sync API'
      );
      // Still set the focused user, but don't pass any groups
      assert.calledWith(
        fakeClientRPC.setFocusedUser,
        fakeStudents[0],
        /* groups */ null
      );
    });
  });

  it('does not set a focus user when the user index is invalid', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find('StudentSelector').props().onSelectStudent(-1); // invalid choice
    });

    assert.calledWith(
      fakeClientRPC.setFocusedUser,
      null /* user */,
      null /* groups */
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderGrader(),
    })
  );
});
