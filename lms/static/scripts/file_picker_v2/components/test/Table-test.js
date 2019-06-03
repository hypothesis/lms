import { createElement } from 'preact';
import { mount } from 'enzyme';

import Table from '../Table';

describe('Table', () => {
  const renderTable = (props = {}) =>
    mount(
      <Table
        columns={[{ label: 'Item' }]}
        items={[]}
        renderItem={item => item}
        {...props}
      />
    );

  it('renders column headings', () => {
    const wrapper = renderTable({
      columns: [{ label: 'Name' }, { label: 'Size' }],
    });
    const columns = wrapper.find('thead th').map(col => col.text());
    assert.deepEqual(columns, ['Name', 'Size']);
  });

  it('renders items', () => {
    const wrapper = renderTable({
      columns: [{ label: 'Item' }],
      items: ['One', 'Two', 'Three'],
      // eslint-disable-next-line react/display-name
      renderItem: item => <span>{item}</span>,
    });

    const items = wrapper.find('tr > span');
    assert.equal(items.length, 3);
    assert.isTrue(wrapper.contains(<span>One</span>));
    assert.isTrue(wrapper.contains(<span>Two</span>));
    assert.isTrue(wrapper.contains(<span>Three</span>));
  });

  ['click', 'mousedown'].forEach(event => {
    it(`selects item on ${event}`, () => {
      const onSelectItem = sinon.stub();
      const wrapper = renderTable({
        items: ['One', 'Two', 'Three'],
        onSelectItem,
      });

      wrapper
        .find('tbody > tr')
        .first()
        .simulate(event);

      assert.calledWith(onSelectItem, 'One');
    });
  });

  it('uses selected item on double-click', () => {
    const item = 'Test item';
    const onUseItem = sinon.stub();
    const wrapper = renderTable({ items: [item], onUseItem });

    wrapper
      .find('tbody > tr')
      .first()
      .simulate('dblclick');

    assert.calledWith(onUseItem, item);
  });

  it('supports keyboard navigation', () => {
    const onSelectItem = sinon.stub();
    const onUseItem = sinon.stub();
    const items = ['One', 'Two', 'Three'];
    const wrapper = renderTable({
      items,
      selectedItem: items[1],
      onSelectItem,
      onUseItem,
    });

    // Down arrow should select item below selected item.
    wrapper.find('table').simulate('keydown', { key: 'ArrowDown' });
    assert.calledWith(onSelectItem, items[2]);

    // Up arrow should select item above selected item.
    onSelectItem.reset();
    wrapper.find('table').simulate('keydown', { key: 'ArrowUp' });
    assert.calledWith(onSelectItem, items[0]);

    // Enter should use selected item.
    onSelectItem.reset();
    wrapper.find('table').simulate('keydown', { key: 'Enter' });
    assert.calledWith(onUseItem, items[1]);

    // Up arrow should not change selection if first item is selected.
    wrapper.setProps({ selectedItem: items[0] });
    onSelectItem.reset();
    wrapper.find('table').simulate('keydown', { key: 'ArrowUp' });
    assert.calledWith(onSelectItem, items[0]);

    // Down arrow should not change selection if last item is selected.
    wrapper.setProps({ selectedItem: items[items.length - 1] });
    onSelectItem.reset();
    wrapper.find('table').simulate('keydown', { key: 'ArrowDown' });
    assert.calledWith(onSelectItem, items[items.length - 1]);

    // Other keys should do nothing.
    onSelectItem.reset();
    wrapper.find('table').simulate('keydown', { key: 'Tab' });
    assert.notCalled(onSelectItem);
  });
});
