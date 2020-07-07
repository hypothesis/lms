import { createElement } from 'preact';
import { mount } from 'enzyme';

import ErrorDisplay, { $imports } from '../ErrorDisplay';
import { checkAccessibility } from '../../../test-util/accessibility';
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

  [
    { message: '' },
    { message: 'Oh no', details: null },
    { message: 'Oh no', details: '' },
  ].forEach(error => {
    it('omits technical details if not provided', () => {
      const wrapper = mount(
        <ErrorDisplay message="Something went wrong" error={error} />
      );

      const details = wrapper.find('pre');
      assert.isFalse(details.exists());
    });
  });

  [
    {
      details: 'Note from server',
      expectedText: 'Note from server',
    },
    {
      details: { statusCode: 123 },
      expectedText: '{ "statusCode": 123 }',
    },
  ].forEach(({ details, expectedText }) => {
    it('displays technical details if provided', () => {
      const error = { message: '', details };

      const wrapper = mount(
        <ErrorDisplay message="Something went wrong" error={error} />
      );

      const detailsEl = wrapper.find('pre');
      assert.isTrue(detailsEl.exists());
      assert.include(detailsEl.text().replace(/\s+/g, ' '), expectedText);
    });
  });

  it('scrolls details into view when opened', () => {
    const error = { message: '', details: 'Note from server' };

    const wrapper = mount(
      <ErrorDisplay message="Something went wrong" error={error} />
    );

    const details = wrapper.find('details');
    const scrollIntoView = sinon.stub(details.getDOMNode(), 'scrollIntoView');

    details.getDOMNode().open = true;
    details.simulate('toggle');

    assert.called(scrollIntoView);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      // eslint-disable-next-line react/display-name
      content: () => (
        <ErrorDisplay
          message="Something went wrong"
          error={new Error('Oh no')}
        />
      ),
    })
  );
});
