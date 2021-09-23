import { mount } from 'enzyme';

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
    assert.include(wrapper.text(), 'An error occurred');
  });

  it('shows dialog for reused_consumer_key', () => {
    fakeConfig.errorCode = 'reused_consumer_key';

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      "This Hypothesis installation's consumer key appears to have"
    );
  });
});
