import { mount } from 'enzyme';
import { createElement } from 'preact';

import { Config } from '../../config';

import CanvasAuthErrorApp from '../CanvasAuthErrorApp';

describe('CanvasAuthErrorApp', () => {
  let fakeConfig;

  const renderApp = () => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <CanvasAuthErrorApp />
      </Config.Provider>
    );
  };

  beforeEach(() => {
    fakeConfig = {
      invalidScope: false,
      authUrl: null,
      scopes: [],
    };
  });

  it('shows a scope error if the scope is invalid', () => {
    fakeConfig.invalidScope = true;
    fakeConfig.scopes = ['scope_a', 'scope_b'];

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      "A Canvas admin needs to edit Hypothesis's developer key"
    );
    fakeConfig.scopes.forEach(scope => assert.include(wrapper.text(), scope));
  });

  it('shows a generic error if the scope is valid', () => {
    const wrapper = renderApp();
    assert.notInclude(wrapper.text(), 'A Canvas admin needs to edit');
  });

  it('renders error details', () => {
    fakeConfig.errorDetails = 'Technical details';

    const wrapper = renderApp();

    const errorDisplay = wrapper.find('ErrorDisplay');
    assert.include(errorDisplay.props(), {
      message: 'Something went wrong when authorizing Hypothesis',
    });
    assert.deepEqual(errorDisplay.prop('error'), {
      details: fakeConfig.errorDetails,
    });
  });
});
