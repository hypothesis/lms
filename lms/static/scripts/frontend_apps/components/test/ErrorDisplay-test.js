import { Link } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import ErrorDisplay, { $imports } from '../ErrorDisplay';

describe('ErrorDisplay', () => {
  let fakeFormatErrorDetails;
  let fakeFormatErrorMessage;
  let fakeConfig;

  beforeEach(() => {
    fakeFormatErrorDetails = sinon.stub().returns('error details');
    fakeFormatErrorMessage = sinon.stub().returns('error message');
    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../errors': {
        formatErrorDetails: fakeFormatErrorDetails,
        formatErrorMessage: fakeFormatErrorMessage,
      },
    });
    fakeConfig = {
      debug: {},
    };
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderErrorDisplay = (props = {}) => {
    return mount(
      <Config.Provider value={fakeConfig}>
        <ErrorDisplay {...props} />
      </Config.Provider>,
    );
  };

  it('provides a formatted support link for generic JavaScript errors', () => {
    fakeFormatErrorDetails.returns('');
    fakeFormatErrorMessage.returns('Failed to fetch files: Canvas says no');
    delete fakeConfig.debug;

    const wrapper = renderErrorDisplay({
      description: 'Failed to fetch files',
      error: new Error(),
    });

    const link = wrapper
      .find(Link)
      .filterWhere(n => n.text() === 'open a support ticket');
    assert.isTrue(link.exists());

    const url = new URL(link.prop('href'));
    assert.equal(url.searchParams.get('product'), 'LMS_app');
    assert.equal(
      url.searchParams.get('subject'),
      '(LMS Error) Failed to fetch files: Canvas says no',
    );

    // No data to put into `content`
    assert.isNull(url.searchParams.get('content'));
  });

  it('provides a formatted support link for errors from our backend', () => {
    fakeFormatErrorDetails.returns('foo: bar');
    fakeFormatErrorMessage.returns('Failed to fetch files: Canvas says no');
    const error = new Error('');
    // Build an ErrorLike object that resembles an APIError
    error.errorCode = 'some_backend_error_code';

    const wrapper = renderErrorDisplay({
      description: 'Failed to fetch files',
      error: error,
    });

    const link = wrapper
      .find(Link)
      .filterWhere(n => n.text() === 'open a support ticket');

    const url = new URL(link.prop('href'));

    assert.include(
      url.searchParams.get('content'),
      'Error code: some_backend_error_code',
    );
    assert.include(
      url.searchParams.get('content'),
      'foo: bar',
      'Includes details',
    );
  });

  it('omits support link when displaySupportLink is false', () => {
    const error = new Error('');
    const wrapper = renderErrorDisplay({
      description: 'Failed to fetch files',
      error: error,
      displaySupportLink: false,
    });

    assert.isFalse(wrapper.exists('[data-testid="error-links"]'));
  });

  it('omits technical details if not provided', () => {
    fakeFormatErrorDetails.returns('');
    const wrapper = renderErrorDisplay({
      description: 'Something went wrong',
      error: { message: '' },
    });

    const details = wrapper.find('[data-testid="error-details"]');
    assert.isFalse(details.exists());
  });

  it('displays technical details if provided', () => {
    const details = 'Some details';
    fakeFormatErrorDetails.returns(details);
    const error = { message: '', details };

    const wrapper = renderErrorDisplay({
      description: 'Something went wrong',
      error: error,
    });

    assert.calledWith(fakeFormatErrorDetails, error);
    const detailsEl = wrapper.find('[data-testid="error-details"]');
    assert.isTrue(detailsEl.exists());
    assert.include(detailsEl.text(), details);
  });

  it('scrolls details into view when opened', () => {
    const error = { message: '', details: 'Note from server' };

    const wrapper = renderErrorDisplay({
      description: 'Something went wrong',
      error: error,
    });

    assert.calledWith(fakeFormatErrorDetails, error);
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
    const wrapper = renderErrorDisplay({
      description: 'foo',
      error: { message: 'whatnot' },
    });

    assert.equal(
      wrapper.find('[data-testid="error-message"]').text(),
      'Hello.',
    );

    assert.calledOnce(fakeFormatErrorMessage);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () =>
        renderErrorDisplay({
          description: 'Something went wrong',
          error: Error('Oh no'),
        }),
    }),
  );
});
