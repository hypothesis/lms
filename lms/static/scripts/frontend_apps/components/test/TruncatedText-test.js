import { mount } from '@hypothesis/frontend-testing';

import TruncatedText from '../TruncatedText';

describe('TruncatedText', () => {
  function createComponent(content, title) {
    const wrapper = mount(
      <div className="flex w-96">
        <TruncatedText title={title}>{content}</TruncatedText>
      </div>,
      { connected: true },
    );
    return wrapper.find('[data-testid="truncated-text"]');
  }

  [
    { content: 'short', isTruncated: false },
    { content: 'long'.repeat(100), isTruncated: true },
  ].forEach(({ content, isTruncated }) => {
    it('adds title when content gets truncated', () => {
      const wrapper = createComponent(content);
      assert.equal(wrapper.prop('title'), isTruncated ? content : undefined);
    });

    it('favors explicitly provided title regardless of whether text is truncated', () => {
      const wrapper = createComponent(content, 'Provided title');
      assert.equal(wrapper.prop('title'), 'Provided title');
    });
  });
});
