import { Fragment, createElement } from 'preact';
import { shallow } from 'enzyme';

import SubmitGradeForm, { $imports } from '../SubmitGradeForm';

describe('SubmitGradeForm', () => {
  const fakeStudent = {
    userid: 'student1',
    displayName: 'Student 1',
    LISResultSourcedId: 1,
    LISOutcomeServiceUrl: '',
  };
  const renderForm = (props = {}) => {
    return shallow(<SubmitGradeForm student={fakeStudent} {...props} />);
  };

  // eslint-disable-next-line react/prop-types
  const FakeErrorDialog = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  // eslint-disable-next-line react/prop-types
  const FakeSpinner = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  // eslint-disable-next-line react/prop-types
  const FakeValidationMessage = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  const fakeSubmitGrade = sinon.stub().resolves({});
  const fakeFetchGrade = sinon.stub().resolves({});
  const fakeValidateGrade = sinon.stub();
  const fakeFormatToNumber = sinon.stub();

  beforeEach(() => {
    $imports.$mock({
      './ErrorDialog': FakeErrorDialog,
      './Spinner': FakeSpinner,
      './ValidationMessage': FakeValidationMessage,
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

  context('validation messages', () => {
    it('hides the validation message by default', () => {
      const wrapper = renderForm();
      assert.isFalse(wrapper.find(FakeValidationMessage).prop('open'));
    });

    it('shows the validation message when the validator returns an error', () => {
      $imports.$mock({
        '../utils/validation': {
          validateGrade: sinon.stub().returns('err'),
        },
      });
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      assert.isTrue(wrapper.find(FakeValidationMessage).prop('open'));
      assert.equal(wrapper.find(FakeValidationMessage).prop('message'), 'err');
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
      assert.isFalse(wrapper.find(FakeValidationMessage).prop('open'));
    });
  });

  context('when submitting a grade', () => {
    beforeEach(() => {
      fakeSubmitGrade.resolves({});
    });
    it('shows the loading spinner when submitting a grade', () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      assert.isTrue(
        wrapper.find('.SubmitGradeForm__loading-backdrop FakeSpinner').exists()
      );
    });

    it('shows the error dialog when the grade request throws an error', () => {
      const wrapper = renderForm();
      fakeSubmitGrade.throws({ errorMessage: '' });
      wrapper.find('button').simulate('click');
      assert.isTrue(wrapper.find(FakeErrorDialog).exists());
    });

    it('sets the `SubmitGradeForm__grade--saved` class when the grade has posted', async () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      try {
        await fakeSubmitGrade.resolves();
      } catch (e) {
        // pass
      }
      assert.isTrue(
        wrapper.find('input').hasClass('SubmitGradeForm__grade--saved')
      );
    });

    it('removes the `SubmitGradeForm__grade--saved` class after the student prop changes', async () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      try {
        await fakeSubmitGrade.resolves();
        wrapper.setProps({ student: {} });
      } catch (e) {
        // pass
      }
      assert.isFalse(
        wrapper.find('input').hasClass('SubmitGradeForm__grade--saved')
      );
    });

    it('xx closes the spinner after the grade has posted', async () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      try {
        await fakeSubmitGrade.resolves();
        wrapper.update();
      } catch (e) {
        // this test fails unless we wrap it in a try/catch
      }
      assert.isFalse(wrapper.find('.SubmitGradeForm__submit-spinner').exists());
    });
  });

  context('when fetching a grade', () => {
    it('sets the class on the <Spinner> component `active` while the grade is fetching', () => {
      const wrapper = renderForm();
      assert.isTrue(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find(FakeSpinner)
          .props('classNames')
          .className.includes('SubmitGradeForm__fetch-spinner--active')
      );
    });

    it('removes the `active` class on the <Spinner> component after the grade has fetched', async () => {
      const wrapper = renderForm();
      try {
        await fakeFetchGrade.resolves({ currentScore: 1 });
      } catch (e) {
        // pass
      }
      assert.isFalse(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find(FakeSpinner)
          .props('classNames')
          .className.includes('SubmitGradeForm__fetch-spinner--active')
      );
    });

    it('sets the class on the <Spinner> component to `fade-away` after the grade has fetched', async () => {
      const wrapper = renderForm();
      try {
        await fakeFetchGrade.resolves({ currentScore: 1 });
      } catch (e) {
        // pass
      }
      assert.isTrue(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find(FakeSpinner)
          .props('classNames')
          .className.includes('SubmitGradeForm__fetch-spinner--fade-away')
      );
    });

    it('does not add the `fade-away` class to the <Spinner> component while the grade is fetching', async () => {
      const wrapper = renderForm();
      assert.isFalse(
        wrapper
          .find('.SubmitGradeForm__grade-wrapper')
          .find(FakeSpinner)
          .props('classNames')
          .className.includes('SubmitGradeForm__fetch-spinner--fade-away')
      );
    });
  });
});
