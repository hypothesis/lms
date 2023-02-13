import { mount } from 'enzyme';

import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';
import { Config } from '../../config';
import AssignmentToolbar, { $imports } from '../AssignmentToolbar';

describe('AssignmentToolbar', () => {
  let fakeConfig;
  let fakeStudents;
  let fakeClientRPC;

  beforeEach(() => {
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

    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderToolbar = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <AssignmentToolbar
          students={fakeStudents}
          courseName={'course name'}
          assignmentName={'course assignment'}
          clientRPC={fakeClientRPC}
          {...props}
        >
          <div title="The assignment content iframe" />
        </AssignmentToolbar>
      </Config.Provider>
    );
  };

  it('sets the assignment and course names', () => {
    const wrapper = renderToolbar();
    assert.equal(
      wrapper.find('[data-testid="assignment-name"]').text(),
      'course assignment'
    );
    assert.equal(
      wrapper.find('[data-testid="course-name"]').text(),
      'course name'
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderToolbar(),
    })
  );
});
