import { MultiSelect } from '@hypothesis/frontend-shared';
import { mount } from 'enzyme';

import PaginatedMultiSelect from '../PaginatedMultiSelect';

describe('PaginatedMultiSelect', () => {
  let wrappers;
  let containers;

  beforeEach(() => {
    wrappers = [];
    containers = [];
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    containers.forEach(c => c.remove());
  });

  function createComponent(props) {
    const container = document.createElement('div');
    containers.push(container);
    document.body.appendChild(container);

    const wrapper = mount(
      <PaginatedMultiSelect
        entity="courses"
        value={[]}
        onChange={sinon.stub()}
        renderOption={o => (
          <MultiSelect.Option value={o}>{o}</MultiSelect.Option>
        )}
        {...props}
      />,
      { attachTo: container },
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  function getSelect(wrapper, id = 'courses') {
    return wrapper.find(`MultiSelect[data-testid="${id}-select"]`);
  }

  function getOpenSelect(wrapper, id = 'courses') {
    const select = getSelect(wrapper, id);
    select.find('button').simulate('click');
    const options = wrapper.find('[role="option"]');

    return { select, options };
  }

  it('renders options based on result data', () => {
    const resultData = ['foo', 'bar', 'baz'];
    const expectedOptions = ['All courses', ...resultData];
    const wrapper = createComponent({
      result: {
        data: resultData,
      },
    });
    const { options } = getOpenSelect(wrapper);

    assert.equal(options.length, expectedOptions.length);
    options.forEach((option, index) => {
      assert.equal(option.text(), expectedOptions[index]);
    });
  });

  [true, false].forEach(isLoading => {
    it('shows page loading indicators when loading', () => {
      const wrapper = createComponent({
        result: { isLoading },
      });

      // Loading indicator is displayed in Select listbox, so we need to open
      // it first
      getOpenSelect(wrapper);

      assert.equal(wrapper.exists('LoadingOption'), isLoading);
    });
  });

  context('when scrolling listboxes down', () => {
    function getScrollableSelect() {
      const fakeLoadNextPage = sinon.stub();
      const wrapper = createComponent({
        result: {
          loadNextPage: fakeLoadNextPage,
          data: ['foo', 'bar', 'baz'],
        },
      });
      const select = getSelect(wrapper);

      return { select, fakeLoadNextPage };
    }

    function scrollTo(select, scrollHeight) {
      select.props().onListboxScroll({
        target: {
          scrollTop: 100,
          clientHeight: 50,
          scrollHeight,
        },
      });
    }

    it('loads next page when scroll is at the bottom', () => {
      const { select, fakeLoadNextPage } = getScrollableSelect();

      scrollTo(select, 160);
      assert.called(fakeLoadNextPage);
    });

    it('does nothing when scroll is not at the bottom', () => {
      const { select, fakeLoadNextPage } = getScrollableSelect();

      scrollTo(select, 250);
      assert.notCalled(fakeLoadNextPage);
    });
  });

  it('displays only active item if provided', () => {
    const wrapper = createComponent({
      activeItem: 'This is displayed',
      // Result is ignored
      result: {
        data: ['foo', 'bar', 'baz'],
      },
    });
    const { options } = getOpenSelect(wrapper);

    assert.equal(options.length, 2);
    assert.equal(options.at(0).text(), 'All courses');
    assert.equal(options.at(1).text(), 'This is displayed');
  });

  describe('error handling', () => {
    let fakeRetry;

    beforeEach(() => {
      fakeRetry = sinon.stub();
    });

    function createComponentWithError() {
      return createComponent({
        result: {
          isLoading: false,
          error: new Error('An error occurred'),
          retry: fakeRetry,
        },
      });
    }

    function clickRetry(wrapper) {
      wrapper.find('button[data-testid="retry-button"]').simulate('click');
    }

    it('shows error message when loading filters fails', () => {
      const wrapper = createComponentWithError();

      // Loading errors are displayed in Select listbox, so we need to open
      // it first
      getOpenSelect(wrapper);

      assert.isTrue(wrapper.exists('LoadingError'));
    });

    it('retries loading when retry button is clicked', () => {
      const wrapper = createComponentWithError();

      // Retry button is displayed in Select listbox, so we need to open it
      // first
      getOpenSelect(wrapper);

      clickRetry(wrapper);
      assert.called(fakeRetry);
    });

    it('focuses last option when retry button is clicked', () => {
      const wrapper = createComponentWithError();
      const { options } = getOpenSelect(wrapper);

      const lastOption = options.last().getDOMNode();
      const focusOption = sinon.stub(lastOption, 'focus');

      clickRetry(wrapper);
      assert.called(focusOption);
    });
  });
});
