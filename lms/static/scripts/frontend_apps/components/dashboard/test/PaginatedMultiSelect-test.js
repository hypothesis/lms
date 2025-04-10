import { MultiSelect } from '@hypothesis/frontend-shared';
import { mount } from '@hypothesis/frontend-testing';

import PaginatedMultiSelect from '../PaginatedMultiSelect';

describe('PaginatedMultiSelect', () => {
  function createComponent(props) {
    return mount(
      <PaginatedMultiSelect
        entity="courses"
        value={[]}
        onChange={sinon.stub()}
        renderOption={o => (
          <MultiSelect.Option value={o}>{o}</MultiSelect.Option>
        )}
        {...props}
      />,
      { connected: true },
    );
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

    function scrollTo(select, { scrollHeight, scrollTop = 100 }) {
      select.props().onPopoverScroll({
        target: {
          clientHeight: 50,
          scrollTop,
          scrollHeight,
        },
      });
    }

    it('loads next page when scroll is at the bottom', () => {
      const { select, fakeLoadNextPage } = getScrollableSelect();

      scrollTo(select, { scrollHeight: 160 });
      assert.called(fakeLoadNextPage);
    });

    it('does nothing when scroll is not at the bottom', () => {
      const { select, fakeLoadNextPage } = getScrollableSelect();

      scrollTo(select, { scrollHeight: 250 });
      assert.notCalled(fakeLoadNextPage);
    });

    it('does not scroll again if scrolling up', () => {
      const { select, fakeLoadNextPage } = getScrollableSelect();

      // We scroll down, then a little bit up, still inside the offset gap
      scrollTo(select, { scrollHeight: 160, scrollTop: 155 });
      scrollTo(select, { scrollHeight: 160, scrollTop: 150 });

      // The page is attempted to load only once, and ignored when scrolling up
      assert.calledOnce(fakeLoadNextPage);
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
