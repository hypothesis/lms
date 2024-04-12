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
      </Config.Provider>,
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
      "This Hypothesis installation's consumer key appears to have",
    );
  });
  it('shows dialog for vital_source_student_pay_no_license', () => {
    fakeConfig.errorCode = 'vitalsource_student_pay_no_license';

    const wrapper = renderApp();
    assert.include(
      wrapper.text(),
      "You don't have license from VitalSource for the Hypothesis app",
    );
  });

  it('shows dialog for vital_source_student_pay_license_launch', () => {
    fakeConfig.errorCode = 'vitalsource_student_pay_license_launch';

    const wrapper = renderApp();
    assert.include(wrapper.text(), 'You now have a license for Hypothesis');
  });
});
