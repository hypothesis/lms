import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import JSTORPicker, { $imports } from '../JSTORPicker';

describe('JSTORPicker', () => {
  let fakeToJSTORUrl;

  function interact(wrapper, callback) {
    act(callback);
    wrapper.update();
  }

  const renderJSTORPicker = (props = {}) => mount(<JSTORPicker {...props} />);

  beforeEach(() => {
    fakeToJSTORUrl = sinon.stub().returns('jstor://1234');

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/jstor': {
        toJSTORUrl: fakeToJSTORUrl,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getInput = wrapper => wrapper.find('TextInput').find('input');

  // Set the value of the input field but do not fire any events
  const setURL = (wrapper, url) => {
    const input = getInput(wrapper);
    input.getDOMNode().value = url;
  };

  // Set the value of the input field AND fire `change` event
  const updateURL = (wrapper, url) => {
    setURL(wrapper, url);
    const input = getInput(wrapper);
    input.simulate('change');
  };

  describe('initial focus', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      document.body.appendChild(container);
    });

    afterEach(() => {
      container.remove();
    });

    it('focuses the URL text input element', () => {
      const beforeFocused = document.activeElement;

      const wrapper = mount(<JSTORPicker onSelectURL={sinon.stub()} />, {
        attachTo: container,
      });

      const focused = document.activeElement;
      const input = wrapper.find('input[name="jstorURL"]').getDOMNode();

      assert.notEqual(beforeFocused, focused);
      assert.equal(focused, input);
    });
  });

  context('entering, changing and submitting article URL', () => {
    it('validates entered URL when the value of the text input changes', () => {
      const wrapper = renderJSTORPicker();

      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeToJSTORUrl);
      assert.calledWith(fakeToJSTORUrl, 'foo');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeToJSTORUrl.callCount,
        2,
        're-validates if entered URL value changes'
      );
      assert.calledWith(fakeToJSTORUrl, 'bar');

      updateURL(wrapper, 'bar');

      assert.equal(
        fakeToJSTORUrl.callCount,
        2,
        'Does not validate URL if it has not changed from previous value'
      );
    });

    it('validates entered URL when input is focused and "Enter" is pressed', () => {
      const wrapper = renderJSTORPicker();
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'https://www.jstor.org/stable/1234');

      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(fakeToJSTORUrl);
      assert.calledWith(fakeToJSTORUrl, 'https://www.jstor.org/stable/1234');
    });

    it('confirms the validated URL if "Enter" is pressed subsequently', () => {
      const onSelectURL = sinon.stub();
      const wrapper = renderJSTORPicker({ onSelectURL });
      const input = getInput(wrapper);
      const keyEvent = new Event('keydown');
      keyEvent.key = 'Enter';

      setURL(wrapper, 'https://www.jstor.org/stable/1234');

      // First enter press will validate URL
      interact(wrapper, () => {
        input.getDOMNode().dispatchEvent(keyEvent);
      });

      assert.calledOnce(fakeToJSTORUrl);

      // Second enter press should "confirm" the valid URL
      input.getDOMNode().dispatchEvent(keyEvent);

      assert.calledOnce(onSelectURL);
      assert.calledWith(onSelectURL, 'jstor://1234');
    });

    it('validates entered URL when `IconButton` is clicked', () => {
      const wrapper = renderJSTORPicker();
      setURL(wrapper, 'foo');

      wrapper.find('IconButton button[title="Find article"]').simulate('click');

      assert.calledOnce(fakeToJSTORUrl);
      assert.calledWith(fakeToJSTORUrl, 'foo');
    });

    it('does not attempt to check the URL format if the field value is empty', () => {
      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      assert.calledOnce(fakeToJSTORUrl);

      updateURL(wrapper, '');

      assert.calledOnce(fakeToJSTORUrl);
    });

    it('shows an error if entered URL format is invalid', () => {
      fakeToJSTORUrl.returns(null);

      const wrapper = renderJSTORPicker();
      updateURL(wrapper, 'foo');

      const errorMessage = wrapper.find('[data-testid="error-message"]');

      assert.isTrue(errorMessage.exists());
      assert.include(
        errorMessage.text(),
        "That doesn't look like a JSTOR article link"
      );
      assert.isTrue(errorMessage.find('Icon[name="cancel"]').exists());
    });
  });

  it('enables submit button when a valid JSTOR URL is entered', () => {
    const wrapper = renderJSTORPicker();
    const buttonSelector = 'LabeledButton[data-testid="select-button"]';

    assert.isTrue(wrapper.find(buttonSelector).props().disabled);

    interact(wrapper, () => {
      updateURL(wrapper, 'foo');
    });

    assert.isFalse(wrapper.find(buttonSelector).props().disabled);
    assert.equal(wrapper.find(buttonSelector).text(), 'Submit');
  });
});
