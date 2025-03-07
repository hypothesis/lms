import { mount } from '@hypothesis/frontend-testing';

import Breadcrumbs from '../Breadcrumbs';

describe('Breadcrumbs', () => {
  const itemFixtures = ['Thing 1', 'Thing 2', 'Thing 3', 'Thing 4'];
  let fakeOnSelectItem;

  const renderBreadcrumbs = (props = {}) =>
    mount(
      <Breadcrumbs
        items={itemFixtures}
        onSelectItem={fakeOnSelectItem}
        renderItem={item => item}
        {...props}
      />,
    );

  beforeEach(() => {
    fakeOnSelectItem = sinon.stub();
  });

  it('renders each item as a button', () => {
    const wrapper = renderBreadcrumbs();

    assert.equal(wrapper.find('button').length, 4);
  });

  it('renders empty if no items are provided', () => {
    const emptyItems = [];
    const wrapper = renderBreadcrumbs({ items: emptyItems });

    assert.isTrue(wrapper.find('Breadcrumbs').isEmptyRender());
  });

  it('disables the selection of the last item', () => {
    const wrapper = renderBreadcrumbs();

    assert.isTrue(wrapper.find('LinkButton').last().props().disabled);
  });

  it('invokes the onSelectItem callback when one of the items is clicked', () => {
    const wrapper = renderBreadcrumbs();

    wrapper.find('button').first().props().onClick();
    assert.calledOnce(fakeOnSelectItem);
    assert.calledWith(fakeOnSelectItem, itemFixtures[0]);
  });

  it('renders items using the provided callback', () => {
    const wrapper = renderBreadcrumbs({
      renderItem: item => `whee ${item} whee`,
    });

    assert.equal(wrapper.find('button').first().text(), 'whee Thing 1 whee');
  });
});
