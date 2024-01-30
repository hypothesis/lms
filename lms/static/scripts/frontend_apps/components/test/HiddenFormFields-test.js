import { mount } from 'enzyme';

import HiddenFormFields from '../HiddenFormFields';

describe('HiddenFormFields', () => {
  const fields = { JWT: 'JWT', VERSION: '1.3.0' };

  function createComponent(props = {}) {
    return mount(<HiddenFormFields fields={fields} {...props} />);
  }
  it('renders form fields', () => {
    const formFields = createComponent();

    Object.entries(fields).forEach(([name, value]) => {
      const field = formFields
        .find('input[type="hidden"]')
        .filter(`[name="${name}"]`);
      assert.isTrue(field.exists());
      assert.equal(field.prop('value'), value);
    });
  });
});
