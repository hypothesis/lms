import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import URLPicker from '../URLPicker';

describe('URLPicker', () => {
  const renderURLPicker = (props = {}) => mount(<URLPicker {...props} />);

  function changeInput(wrapper, value) {
    const input = wrapper.find('input');
    input.getDOMNode().value = value;
    input.simulate('change');
  }

  function submitForm(wrapper) {
    wrapper.find('form').simulate('submit');
    wrapper.update();
  }

  function getError(wrapper) {
    return wrapper.find('UIMessage[status="error"]').text();
  }

  function hasError(wrapper) {
    return wrapper.exists('UIMessage[status="error"]');
  }

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderURLPicker({
      defaultURL: 'https://arxiv.org/pdf/1234.pdf',
    });
    assert.equal(
      wrapper.find('input').getDOMNode().value,
      'https://arxiv.org/pdf/1234.pdf',
    );
  });

  it('does not display an error if the URL is valid', () => {
    const onSelectURL = sinon.stub();
    const wrapper = renderURLPicker({ onSelectURL });
    changeInput(wrapper, 'https://example.com/foo');
    assert.isFalse(hasError(wrapper));
  });

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderURLPicker({ onSelectURL });
    changeInput(wrapper, 'https://example.com/foo');
    submitForm(wrapper);

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('displays error if no URL is entered', () => {
    const wrapper = renderURLPicker({ onSelectURL: sinon.stub() });
    submitForm(wrapper);
    assert.include(getError(wrapper), 'Please enter a URL');
  });

  it('displays error if URL is not valid', () => {
    const wrapper = renderURLPicker({ onSelectURL: sinon.stub() });
    changeInput(wrapper, 'not-a-url');
    assert.include(getError(wrapper), 'Please enter a URL');
  });

  ['', 'not-a-url'].forEach(value => {
    it('does not invoke `onSelectURL` if URL is not valid', () => {
      const onSelectURL = sinon.stub();

      const wrapper = renderURLPicker({ onSelectURL });
      changeInput(wrapper, value);
      submitForm(wrapper);

      assert.notCalled(onSelectURL);
    });
  });

  it('does not invoke `onSelectURL` if URL is for a non-http(s) protocol', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderURLPicker({ onSelectURL });
    changeInput(wrapper, 'ftp:///warez.fun');
    submitForm(wrapper);

    assert.notCalled(onSelectURL);
    assert.include(
      getError(wrapper),
      'Please use a URL that starts with "http" or "https"',
    );
  });

  it('shows an additional error message if URL is for a local file', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderURLPicker({ onSelectURL });
    changeInput(wrapper, 'file:///my/local.pdf');
    submitForm(wrapper);

    assert.notCalled(onSelectURL);
    assert.include(
      getError(wrapper),
      'URLs that start with "file" are files on your own computer.',
    );
  });

  [
    {
      youtubeEnabled: true,
      expectedError:
        'To annotate a video, go back and choose the YouTube option.',
    },
    {
      youtubeEnabled: false,
      expectedError:
        'Annotating YouTube videos has been disabled at your organisation.',
    },
  ].forEach(({ youtubeEnabled, expectedError }) => {
    it('does not invoke `onSelectURL` if URL is for a YouTube video', () => {
      const onSelectURL = sinon.stub();

      const wrapper = renderURLPicker({ onSelectURL, youtubeEnabled });
      changeInput(wrapper, 'https://youtu.be/EU6TDnV5osM');
      submitForm(wrapper);

      assert.notCalled(onSelectURL);
      assert.include(getError(wrapper), expectedError);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderURLPicker(),
    }),
  );
});
