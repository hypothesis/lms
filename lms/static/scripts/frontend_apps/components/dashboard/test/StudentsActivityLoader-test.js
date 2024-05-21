import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import sinon from 'sinon';

import { Config } from '../../../config';
import StudentsActivityLoader, { $imports } from '../StudentsActivityLoader';

describe('StudentsActivityLoader', () => {
  let fakeAPICall;
  let fakeUseParams;
  let fakeConfig;

  beforeEach(() => {
    fakeAPICall = sinon.stub();
    fakeUseParams = sinon.stub().returns({ assignmentId: '123' });
    fakeConfig = {
      api: {
        authToken: 'authToken',
      },
      dashboard: {
        routes: {
          assignment: '/api/assignment/:assignment_id',
          assignment_stats: '/api/assignment/:assignment_id/stats',
        },
      },
    };

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        apiCall: fakeAPICall,
      },
      'wouter-preact': {
        useParams: fakeUseParams,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={fakeConfig}>
        <StudentsActivityLoader />
      </Config.Provider>,
    );
  }

  function triggerOnLoad(wrapper, responses) {
    wrapper.find('DataLoader').props().onLoad(responses);
    wrapper.update();
  }

  function triggerLoad(wrapper) {
    wrapper.find('DataLoader').props().load();
  }

  it('initially shows no StudentsActivity', () => {
    const wrapper = createComponent();

    assert.isFalse(wrapper.exists('StudentsActivity'));
    assert.isFalse(wrapper.find('DataLoader').prop('loaded'));
  });

  it('shows StudentsActivity once data is loaded', () => {
    const wrapper = createComponent();

    triggerOnLoad(wrapper, {
      assignment: {},
      students: [],
    });

    assert.isTrue(wrapper.exists('StudentsActivity'));
    assert.isTrue(wrapper.find('DataLoader').prop('loaded'));
  });

  it('gets assignment and students on load', () => {
    const wrapper = createComponent();

    assert.notCalled(fakeAPICall);
    triggerLoad(wrapper);

    assert.calledTwice(fakeAPICall);
    assert.calledWith(
      fakeAPICall.getCall(0),
      sinon.match({
        authToken: 'authToken',
        path: '/api/assignment/123',
      }),
    );
    assert.calledWith(
      fakeAPICall.getCall(1),
      sinon.match({
        authToken: 'authToken',
        path: '/api/assignment/123/stats',
      }),
    );
  });
});
