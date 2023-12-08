import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../config';
import EmailPreferencesApp, { $imports } from '../EmailPreferencesApp';

describe('EmailPreferencesApp', () => {
  const emailPreferences = {
    mon: true,
    tue: true,
    wed: false,
    thu: false,
    fri: true,
    sat: false,
    sun: true,
  };

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent() {
    return mount(
      <Config.Provider value={{ emailPreferences }}>
        <EmailPreferencesApp />
      </Config.Provider>
    );
  }

  it('loads preferences from config', () => {
    const wrapper = createComponent();
    const preferencesComponent = wrapper.find('EmailPreferences');

    assert.isTrue(preferencesComponent.exists());
    assert.equal(preferencesComponent.prop('selectedDays'), emailPreferences);
  });

  it('allows selected days to be updated', () => {
    const wrapper = createComponent();
    const newSelectedDays = {
      mon: false,
      wed: true,
    };

    wrapper
      .find('EmailPreferences')
      .props()
      .updateSelectedDays(newSelectedDays);
    wrapper.update();

    assert.deepEqual(wrapper.find('EmailPreferences').prop('selectedDays'), {
      ...emailPreferences,
      ...newSelectedDays,
    });
  });

  it('when preferences are saved it sets saving to true', () => {
    const wrapper = createComponent();

    wrapper.find('EmailPreferences').props().onSave();
    wrapper.update();

    assert.isTrue(wrapper.find('EmailPreferences').prop('saving'));
  });
});
