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

  const getSupportEmailLink = wrapper => {
    const supportLink = wrapper
      .find('a')
      .filterWhere(n => n.text() === 'send us an email');
    return new URL(supportLink.prop('href'));
  };

  it('displays a support link', () => {
    const error = new Error('Canvas says no');
    error.details = { someTechnicalDetail: 123 };

    const wrapper = mount(
      <ErrorDisplay message="Failed to fetch files" error={error} />
    );

    const href = getSupportEmailLink(wrapper);

    assert.equal(href.protocol, 'mailto:');
    assert.equal(href.pathname, 'support@hypothes.is');
    assert.equal(href.searchParams.get('subject'), 'Hypothesis LMS support');
    assert.include(href.searchParams.get('body'), 'Canvas says no');
    assert.include(href.searchParams.get('body'), '"someTechnicalDetail": 123');
  });

  it('omits "Error message" from support email body if error has no message', () => {
    const error = new Error('');
    error.details = { someTechnicalDetail: 123 };

    const wrapper = mount(
      <ErrorDisplay message="Failed to fetch files" error={error} />
    );
    const href = getSupportEmailLink(wrapper);

    assert.include(href.searchParams.get('body'), 'Technical details');
    assert.notInclude(href.searchParams.get('body'), 'Error message');
  });

  it('omits "Technical details" from support email body if error has no details', () => {
    const error = new Error('Something went wrong');

    const wrapper = mount(
      <ErrorDisplay message="Failed to fetch files" error={error} />
    );
    const href = getSupportEmailLink(wrapper);

    assert.notInclude(href.searchParams.get('body'), 'Technical details');
    assert.include(href.searchParams.get('body'), 'Error message');
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

    // Details should be scrolled into view if details is opened.
    details.getDOMNode().open = true;
    details.simulate('toggle');
    assert.called(scrollIntoView);

    // Details should not be scrolled into view if details is closed.
    scrollIntoView.resetHistory();
    details.getDOMNode().open = false;
    details.simulate('toggle');
    assert.notCalled(scrollIntoView);
  });

  [
    {
      message: 'Not a sentence',
      output: 'Not a sentence.',
    },
    {
      message: 'A sentence',
      output: 'A sentence.',
    },
    {
      message: 'Oh no',
      error: 'Tech details',
      output: 'Oh no: Tech details.',
    },
    {
      message: 'Oh no',
      error: 'Tech details.',
      output: 'Oh no: Tech details.',
    },
  ].forEach(({ message, error, output }, index) => {
    it(`formats errors as sentences (${index})`, () => {
      const wrapper = mount(
        <ErrorDisplay message={message} error={{ message: error }} />
      );
      assert.equal(wrapper.find('p').first().text(), output);
    });
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
