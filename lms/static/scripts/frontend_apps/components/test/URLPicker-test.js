import { checkAccessibility } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import URLPicker from '../URLPicker';

describe('URLPicker', () => {
  const renderUrlPicker = (props = {}) => mount(<URLPicker {...props} />);

  it('pre-fills input with `defaultURL` prop value', () => {
    const wrapper = renderUrlPicker({
      defaultURL: 'https://arxiv.org/pdf/1234.pdf',
    });
    assert.equal(
      wrapper.find('input').getDOMNode().value,
      'https://arxiv.org/pdf/1234.pdf',
    );
  });

  it('invokes `onSelectURL` when user submits a URL', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'https://example.com/foo';

    wrapper
      .find('button[data-testid="submit-button"]')
      .props()
      .onClick(new Event('click'));

    assert.calledWith(onSelectURL, 'https://example.com/foo');
  });

  it('does not invoke `onSelectURL` if URL is not valid', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'not-a-url';

    wrapper
      .find('button[data-testid="submit-button"]')
      .props()
      .onClick(new Event('click'));
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('UIMessage[status="error"]');
    assert.isTrue(errorMessage.exists());
    assert.include(errorMessage.text(), 'Please enter a URL');
  });

  it('does not invoke `onSelectURL` if URL is for a non-http(s) protocol', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'ftp:///warez.fun';

    wrapper
      .find('button[data-testid="submit-button"]')
      .props()
      .onClick(new Event('click'));
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('UIMessage[status="error"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
      'Please use a URL that starts with "http" or "https"',
    );
  });

  it('shows an additional error message if URL is for a local file', () => {
    const onSelectURL = sinon.stub();

    const wrapper = renderUrlPicker({ onSelectURL });
    wrapper.find('input').getDOMNode().value = 'file:///my/local.pdf';

    wrapper
      .find('button[data-testid="submit-button"]')
      .props()
      .onClick(new Event('click'));
    wrapper.update();

    assert.notCalled(onSelectURL);
    const errorMessage = wrapper.find('UIMessage[status="error"]');
    assert.isTrue(errorMessage.exists());
    assert.include(
      errorMessage.text(),
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

      const wrapper = renderUrlPicker({ onSelectURL, youtubeEnabled });
      wrapper.find('input').getDOMNode().value = 'https://youtu.be/EU6TDnV5osM';

      wrapper
        .find('button[data-testid="submit-button"]')
        .props()
        .onClick(new Event('click'));
      wrapper.update();

      assert.notCalled(onSelectURL);
      const errorMessage = wrapper.find('UIMessage[status="error"]');
      assert.isTrue(errorMessage.exists());
      assert.include(errorMessage.text(), expectedError);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderUrlPicker(),
    }),
  );
});
