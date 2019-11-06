import { createElement } from 'preact';
import { mount } from 'enzyme';

import SubmitGradeForm, { $imports } from '../SubmitGradeForm';
import mockImportedComponents from './mock-imported-components';
import { waitFor } from './util';

describe('SubmitGradeForm', () => {
  const fakeStudent = {
    userid: 'student1',
    displayName: 'Student 1',
    LISResultSourcedId: 1,
    LISOutcomeServiceUrl: '',
  };
  const renderForm = (props = {}) => {
    return mount(<SubmitGradeForm student={fakeStudent} {...props} />);
  };

  const fakeSubmitGrade = sinon.stub().resolves({});
  const fakeFetchGrade = sinon.stub().resolves({ currentScore: 1 });
  const fakeValidateGrade = sinon.stub();
  const fakeFormatToNumber = sinon.stub();

  const isFetchingGrade = wrapper => {
    wrapper.update();
    return wrapper
      .find('Spinner.SubmitGradeForm__fetch-spinner')
      .prop('className')
      .includes('is-active');
  };

  beforeEach(() => {
    // Reset the api grade stubs for each test because
    // some tests below will change these for specific cases.
    fakeSubmitGrade.resolves({});
    fakeFetchGrade.resolves({ currentScore: 1 });

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/grader-service': {
        submitGrade: fakeSubmitGrade,
        fetchGrade: fakeFetchGrade,
      },
      '../utils/validation': {
        formatToNumber: fakeFormatToNumber,
        validateGrade: fakeValidateGrade,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('does not disable the input field when the disable prop is missing', () => {
    const wrapper = renderForm();
    assert.isFalse(wrapper.find('input').prop('disabled'));
  });

  it('disables the submit button when the disable prop is true', () => {
    const wrapper = renderForm({ disabled: true });
    assert.isTrue(wrapper.find('button').prop('disabled'));
  });

  it("sets the input key to the student's LISResultSourcedId", () => {
    const wrapper = renderForm();
    assert.equal(wrapper.find('input').key(), fakeStudent.LISResultSourcedId);
  });

  it('clears out the previous grade when changing students', async () => {
    const wrapper = renderForm();
    await waitFor(() => !isFetchingGrade(wrapper));

    assert.equal(wrapper.find('input').prop('defaultValue'), 10);
    wrapper.setProps({ student: {} });
    assert.equal(wrapper.find('input').prop('defaultValue'), '');
  });

  context('validation messages', () => {
    it('hides the validation message by default', () => {
      const wrapper = renderForm();
      assert.isFalse(wrapper.find('ValidationMessage').prop('open'));
    });

    it('shows the validation message when the validator returns an error', () => {
      $imports.$mock({
        '../utils/validation': {
          validateGrade: sinon.stub().returns('err'),
        },
      });
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      assert.isTrue(wrapper.find('ValidationMessage').prop('open'));
      assert.equal(wrapper.find('ValidationMessage').prop('message'), 'err');
    });

    it('hides the validation message after it was opened when input is detected', () => {
      $imports.$mock({
        '../utils/validation': {
          validateGrade: sinon.stub().returns('err'),
        },
      });
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      wrapper.find('input').simulate('keydown', { key: 'k' });
      assert.isFalse(wrapper.find('ValidationMessage').prop('open'));
    });
  });

  context('when submitting a grade', () => {
    it('shows the loading spinner when submitting a grade', () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      assert.isTrue(
        wrapper.find('.SubmitGradeForm__loading-backdrop Spinner').exists()
      );
    });

    it('shows the error dialog when the grade request throws an error', () => {
      const wrapper = renderForm();
      fakeSubmitGrade.throws({ errorMessage: '' });
      wrapper.find('button').simulate('click');
      assert.isTrue(wrapper.find('ErrorDialog').exists());
    });

    it('sets the `is-saved` class when the grade has posted', async () => {
      const wrapper = renderForm();

      wrapper.find('button').simulate('click');
      await waitFor(() => !isFetchingGrade(wrapper));

      assert.isTrue(wrapper.find('input').hasClass('is-saved'));
    });

    it('removes the `SubmitGradeForm__grade--saved` class after the student prop changes', async () => {
      const wrapper = renderForm();

      wrapper.find('button').simulate('click');
      wrapper.setProps({ student: {} });

      assert.isFalse(
        wrapper.find('input').hasClass('SubmitGradeForm__grade--saved')
      );
    });

    it('closes the spinner after the grade has posted', async () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');

      await waitFor(() => {
        wrapper.update();
        return !wrapper.exists('.SubmitGradeForm__submit-spinner');
      });
    });
  });

  context('when fetching a grade', () => {
    it("sets the input defaultValue prop to the student's grade", async () => {
      const wrapper = renderForm();
      await waitFor(() => !isFetchingGrade(wrapper));
      // note, grade is scaled by 10
      assert.equal(wrapper.find('input').prop('defaultValue'), 10);
    });

    it('sets the class on the <Spinner> component `active` while the grade is fetching', () => {
      const wrapper = renderForm();
      assert.isTrue(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find('Spinner')
          .props('classNames')
          .className.includes('is-active')
      );
    });

    it('sets the class on the <Spinner> component to `fade-away` after the grade has fetched', async () => {
      const wrapper = renderForm();
      await waitFor(() => !isFetchingGrade(wrapper));
      assert.isTrue(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find('Spinner')
          .props('classNames')
          .className.includes('is-fade-away')
      );
    });

    it('does not add the `fade-away` class to the <Spinner> component while the grade is fetching', async () => {
      const wrapper = renderForm();
      assert.isFalse(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find('Spinner')
          .props('classNames')
          .className.includes('SubmitGradeForm__fetch-spinner--fade-away')
      );
    });
  });
});
