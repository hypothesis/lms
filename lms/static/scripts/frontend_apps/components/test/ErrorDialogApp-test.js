import { mount } from 'enzyme';
import { createElement } from 'preact';

import { Config } from '../../config';

import ErrorDialogApp from '../ErrorDialogApp';

describe('ErrorDialogApp', () => {
  let fakeConfig;

  const renderApp = () => {
    const config = {
      errorDialog: fakeConfig,
    };

    return mount(
      <Config.Provider value={config}>
        <ErrorDialogApp />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      errorCode: null,
      errorDetails: '',
    };
  });

  it('shows dialog for unknown error code', () => {
    const wrapper = renderApp();
    assert.include(wrapper.text(), 'Unknown error occurred');
  });

  it('shows dialog for reused tool_consumer_guid', () => {
    fakeConfig.errorCode = 'reused_tool_guid';

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      'The same Hypothesis Consumer Key and Shared Secret has been used previously in another LMS'
    );
  });
});
