import {
  mockImportedComponents,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { useConfig } from '../../config';
import { useService } from '../../services';
import AppRoot, { $imports } from '../AppRoot';

describe('AppRoot', () => {
  let fakeLoadFilePickerConfig;
  let originalURL;
  let wrappers;

  function navigateTo(url) {
    if (location.href !== url) {
      history.replaceState({}, 'unused', url);
    }
  }

  function renderAppRoot({ config, services }) {
    const wrapper = mount(
      <AppRoot initialConfig={config} services={services} />
    );
    wrappers.push(wrapper);
    return wrapper;
  }

  beforeEach(() => {
    fakeLoadFilePickerConfig = sinon.stub().resolves({ filePicker: {} });
    wrappers = [];

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      // Un-mock this component so we can test the whole route-change process.
      './DataLoader': true,
    });

    $imports.$mock({
      './FilePickerApp': { loadFilePickerConfig: fakeLoadFilePickerConfig },
    });

    // Suppress warning when exceptions are thrown when rendering.
    sinon.stub(console, 'warn');

    originalURL = location.href;
  });

  afterEach(() => {
    navigateTo(originalURL);

    // Mounted AppRoot(s) must be unmounted after each test to prevent them
    // from responding to URL changes in subsequent tests.
    wrappers.forEach(w => w.unmount());

    console.warn.restore();
    $imports.$restore();
  });

  [
    {
      config: { mode: 'basic-lti-launch' },
      appComponent: 'BasicLTILaunchApp',
    },
    {
      config: { mode: 'content-item-selection', filePicker: {} },
      appComponent: 'FilePickerApp',
    },
    {
      config: { mode: 'email-notifications' },
      appComponent: 'EmailNotificationsApp',
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
      const wrapper = renderAppRoot({ config, services: new Map() });
      assert.isTrue(wrapper.exists(appComponent));
    });
  });

  it('loads config for file picker after route change', async () => {
    // Mock FilePickerApp to observe config it receives.
    let actualConfig;
    function DummyFilePickerApp() {
      actualConfig = useConfig();
    }
    DummyFilePickerApp.displayName = 'FilePickerApp';
    $imports.$mock({
      './FilePickerApp': DummyFilePickerApp,
    });

    // Simulate a launch that is initially viewing an assignment.
    const config = { mode: 'basic-lti-launch' };
    navigateTo('/app/basic-lti-launch');
    const wrapper = renderAppRoot({ config, services: new Map() });
    assert.isTrue(wrapper.exists('BasicLTILaunchApp'));

    // Navigate to assignment edit route. This should cause the additional
    // configuration needed by that route to be fetched.
    const updatedConfig = { ...config, filePicker: {} };
    fakeLoadFilePickerConfig.resolves(updatedConfig);
    navigateTo('/app/content-item-selection');

    // Once the additional configuration is fetched, the mocked FilePickerApp
    // should be rendered.
    await waitForElement(wrapper, 'FilePickerApp');
    assert.calledOnce(fakeLoadFilePickerConfig);
    assert.equal(actualConfig, updatedConfig);
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

    renderAppRoot({ config, services });

    assert.equal(actualConfig, config);
    assert.equal(actualService, services.get(TestService));
  });

  it('renders "Page not found" message for unknown route', () => {
    const config = { mode: 'invalid' };
    const wrapper = renderAppRoot({ config, services: new Map() });
    assert.isTrue(wrapper.exists('[data-testid="notfound-message"]'));
  });
});
