import { createElement } from 'preact';
import { mount } from 'enzyme';

import ErrorDisplay, { $imports } from '../ErrorDisplay';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('ErrorDisplay', () => {
  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('displays a support link', () => {
    const error = new Error('Canvas says no');
    error.details = { someTechnicalDetail: 123 };

    const wrapper = mount(
      <ErrorDisplay message="Failed to fetch files" error={error} />
    );

    const supportLink = wrapper
      .find('a')
      .filterWhere(n => n.text() === 'send us an email');
    const href = new URL(supportLink.prop('href'));

    assert.equal(href.protocol, 'mailto:');
    assert.equal(href.pathname, 'support@hypothes.is');
    assert.equal(href.searchParams.get('subject'), 'Hypothesis LMS support');
    assert.include(href.searchParams.get('body'), 'Canvas says no');
    assert.include(href.searchParams.get('body'), '"someTechnicalDetail": 123');
  });

  it('omits technical details if not provided', () => {
    const error = { message: '' };

    const wrapper = mount(
      <ErrorDisplay message="Something went wrong" error={error} />
    );

    const details = wrapper.find('pre');
    assert.isFalse(details.exists());
  });

  it('displays technical details if provided', () => {
    const error = { message: '', details: 'Note from server' };

    const wrapper = mount(
      <ErrorDisplay message="Something went wrong" error={error} />
    );

    const details = wrapper.find('pre');
    assert.isTrue(details.exists());
    assert.include(details.text(), 'Note from server');
  });
});
