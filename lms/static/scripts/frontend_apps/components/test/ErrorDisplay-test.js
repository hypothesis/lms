import { mount } from 'enzyme';

import ErrorDisplay, { $imports } from '../ErrorDisplay';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('ErrorDisplay', () => {
  let fakeFormatErrorMessage;

  beforeEach(() => {
    fakeFormatErrorMessage = sinon.stub().returns('error message');
    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../errors': {
        formatErrorMessage: fakeFormatErrorMessage,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('provides a formatted support link for generic JavaScript errors', () => {
    fakeFormatErrorMessage.returns('Failed to fetch files: Canvas says no');

    const wrapper = mount(
      <ErrorDisplay description="Failed to fetch files" error={new Error()} />
    );

    const link = wrapper
      .find('Link')
      .filterWhere(n => n.text() === 'open a support ticket');
    assert.isTrue(link.exists());

    const url = new URL(link.prop('href'));
    assert.equal(url.searchParams.get('product'), 'LMS_app');
    assert.equal(
      url.searchParams.get('subject'),
      '(LMS Error) Failed to fetch files: Canvas says no'
    );

    // No data to put into `content`
    assert.isNull(url.searchParams.get('content'));
  });

  it('provides a formatted support link for errors from our backend', () => {
    fakeFormatErrorMessage.returns('Failed to fetch files: Canvas says no');
    const error = new Error('');
    // Build an ErrorLike object that resembles an APIError
    error.errorCode = 'some_backend_error_code';
    error.details = {
      foo: 'bar',
    };

    const wrapper = mount(
      <ErrorDisplay description="Failed to fetch files" error={error} />
    );

    const link = wrapper
      .find('Link')
      .filterWhere(n => n.text() === 'open a support ticket');

    const url = new URL(link.prop('href'));

    assert.include(
      url.searchParams.get('content'),
      'Error code: some_backend_error_code'
    );
    assert.include(
      url.searchParams.get('content'),
      '"foo": "bar"',
      'Includes details'
    );
  });

  [
    { description: '' },
    { description: 'Oh no', details: null },
    { description: 'Oh no', details: '' },
  ].forEach(error => {
    it('omits technical details if not provided', () => {
      const wrapper = mount(
        <ErrorDisplay
          message="Something went wrong"
          error={{ message: '', details: error.details }}
        />
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

  it('Adds a period to the error message', () => {
    fakeFormatErrorMessage.returns('Hello');
    const wrapper = mount(
      <ErrorDisplay description="foo" error={{ message: 'whatnot' }} />
    );

    assert.equal(
      wrapper.find('[data-testid="error-message"]').text(),
      'Hello.'
    );

    assert.calledOnce(fakeFormatErrorMessage);
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
