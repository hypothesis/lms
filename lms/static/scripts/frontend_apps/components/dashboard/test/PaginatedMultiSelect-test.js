import { MultiSelect } from '@hypothesis/frontend-shared';
import { mount } from 'enzyme';

import PaginatedMultiSelect from '../PaginatedMultiSelect';

describe('PaginatedMultiSelect', () => {
  let wrappers;

  beforeEach(() => {
    wrappers = [];
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
  });

  function createComponent(props) {
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
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  function getSelect(wrapper, id = 'courses') {
    return wrapper.find(`MultiSelect[data-testid="${id}-select"]`);
  }

  it('renders options based on result data', () => {
    const resultData = ['foo', 'bar', 'baz'];
    const expectedOptions = ['All courses', ...resultData];
    const wrapper = createComponent({
      result: {
        data: resultData,
      },
    });
    const select = getSelect(wrapper);
    const options = select.find(MultiSelect.Option);

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
    const select = getSelect(wrapper);
    const options = select.find(MultiSelect.Option);

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
      assert.isTrue(wrapper.exists('LoadingError'));
    });

    it('retries loading when retry button is clicked', () => {
      const wrapper = createComponentWithError();

      clickRetry(wrapper);
      assert.called(fakeRetry);
    });

    it('focuses last option when retry button is clicked', () => {
      const wrapper = createComponentWithError();

      const lastOption = wrapper
        .find(`[data-testid="courses-select"]`)
        .find('[role="option"]')
        .last()
        .getDOMNode();
      const focusOption = sinon.stub(lastOption, 'focus');

      clickRetry(wrapper);
      assert.called(focusOption);
    });
  });
});
