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

  it('provides a formatted support link for generic JavaScript errors', () => {
    const error = new Error('Canvas says no');

    const wrapper = mount(
      <ErrorDisplay description="Failed to fetch files" error={error} />
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
    const error = new Error('Canvas says no');
    // Build an ErrorLike object that resembles an APIError
    error.errorCode = 'some_backend_error_code';
    error.serverMessage = 'A message from the back end';
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
    assert.equal(
      url.searchParams.get('subject'),
      '(LMS Error) Failed to fetch files: A message from the back end'
    );
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

  [
    {
      description: 'Not a sentence',
      error: {},
      output: 'Not a sentence.',
    },
    {
      description: 'A sentence.',
      error: {},
      output: 'A sentence.',
    },
    {
      description: 'Oh no',
      error: {
        message: 'Tech details',
      },
      output: 'Oh no: Tech details.',
    },
    {
      error: {
        message: 'Tech details',
      },
      output: 'Tech details.',
    },
    {
      error: {
        message: 'Default error message',
        serverMessage: 'Server message',
      },
      output: 'Server message.',
    },
    {
      description: 'Something went wrong',
      error: {
        message: 'Default error message',
        serverMessage: 'Server message',
      },
      output: 'Something went wrong: Server message.',
    },
    {
      description: 'Something went wrong',
      error: {
        message: 'Default error message',
        serverMessage: '',
      },
      output: 'Something went wrong.',
    },
    {
      error: {
        message: 'Default error message',
        serverMessage: '',
      },
    },
  ].forEach(({ description, error, output }, index) => {
    it(`formats description and/or message appropriately (${index})`, () => {
      const wrapper = mount(
        <ErrorDisplay description={description} error={error} />
      );
      if (output) {
        assert.equal(
          wrapper.find('p[data-testid="error-message"]').text(),
          output
        );
      } else {
        assert.isFalse(wrapper.find('p[data-testid="error-message"]').exists());
      }
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
