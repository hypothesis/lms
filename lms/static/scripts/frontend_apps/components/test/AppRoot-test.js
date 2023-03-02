import { mount } from 'enzyme';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { useConfig } from '../../config';
import { useService } from '../../services';
import AppRoot, { $imports } from '../AppRoot';

describe('AppRoot', () => {
  let originalURL;

  function navigateTo(url) {
    if (location.href !== url) {
      history.replaceState({}, 'unused', url);
    }
  }

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());

    // Suppress warning when exceptions are thrown when rendering.
    sinon.stub(console, 'warn');

    originalURL = location.href;
  });

  afterEach(() => {
    navigateTo(originalURL);

    console.warn.restore();
    $imports.$restore();
  });

  [
    {
      config: { mode: 'basic-lti-launch' },
      appComponent: 'BasicLTILaunchApp',
    },
    {
      config: { mode: 'content-item-selection' },
      appComponent: 'FilePickerApp',
    },
    {
      config: { mode: 'error-dialog' },
      appComponent: 'ErrorDialogApp',
    },
    {
      config: { mode: 'oauth2-redirect-error' },
      appComponent: 'OAuth2RedirectErrorApp',
    },
  ].forEach(({ config, appComponent }) => {
    it('launches correct app for "mode" config', () => {
      navigateTo(`/app/${config.mode}`);
      const services = new Map();
      const wrapper = mount(
        <AppRoot initialConfig={config} services={services} />
      );
      assert.isTrue(wrapper.exists(appComponent));
    });
  });

  it('exposes config and services to current route', () => {
    class TestService {}
    const services = new Map();
    services.set(TestService, new TestService());

    let actualConfig;
    let actualService;
    function DummyFilePickerApp() {
      actualConfig = useConfig();
      actualService = useService(TestService);
    }

    $imports.$mock({
      './FilePickerApp': DummyFilePickerApp,
    });
    const config = { mode: 'content-item-selection', filePicker: {} };
    navigateTo(`/app/${config.mode}`);

    mount(<AppRoot initialConfig={config} services={services} />);

    assert.equal(actualConfig, config);
    assert.equal(actualService, services.get(TestService));
  });

  it('renders "Page not found" message for unknown route', () => {
    const config = { mode: 'invalid' };
    const wrapper = mount(
      <AppRoot initialConfig={config} services={new Map()} />
    );
    assert.isTrue(wrapper.exists('[data-testid="notfound-message"]'));
  });
});
