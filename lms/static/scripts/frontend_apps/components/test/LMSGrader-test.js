import { createElement } from 'preact';
import { mount } from 'enzyme';

import { Config } from '../../config';
import LMSGrader from '../LMSGrader';


describe('LMSGrader', () => {
  let fakeHypothesisConfig;
  let fakeScriptNode;
  let fakeConfig;
  const fakeOnChange = sinon.stub();

  beforeEach(() => {
    fakeHypothesisConfig = sinon.stub(document, 'querySelector');
    fakeScriptNode = {
      text: JSON.stringify({}), // empty default value
    };
    fakeHypothesisConfig
      .withArgs('.js-hypothesis-config')
      .returns(fakeScriptNode);

    fakeConfig = {
      grading: {
        students: [
          {
            username: 'user1',
            displayName: 'User 1',
          },
          {
            username: 'user2',
            displayName: 'User 2',
          },
        ],
      },
    };
  });

  afterEach(() => {
    fakeHypothesisConfig.restore();
  });

  const renderGrader = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <LMSGrader onChangeUser={fakeOnChange} {...props} />
      </Config.Provider>
    );
  };

  it('sets the first default user to be the focused user in the config', () => {
    renderGrader();
    sinon.assert.match(JSON.parse(fakeScriptNode.text), {
      focus: { user: { username: 'user1', displayName: 'User 1' } },
    });
  });

  it('clicking the next button changes the focus user in the config', () => {
    const wrapper = renderGrader();
    wrapper
      .find('button')
      .last()
      .simulate('click');
    sinon.assert.match(JSON.parse(fakeScriptNode.text), {
      focus: { user: { username: 'user2', displayName: 'User 2' } },
    });
  });
});
