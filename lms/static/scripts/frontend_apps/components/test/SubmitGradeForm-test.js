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
    return shallow(
      <SubmitGradeForm disabled={false} student={fakeStudent} {...props} />
    );
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

  const fakeSubmitGrade = sinon.stub().resolves([]); //sinon.stub();
  const fakeValidateGrade = sinon.stub();
  const fakeFormatToNumber = sinon.stub();

  beforeEach(() => {
    $imports.$mock({
      './ErrorDialog': FakeErrorDialog,
      './Spinner': FakeSpinner,
      './ValidationMessage': FakeValidationMessage,
      '../utils/grader-service': {
        submitGrade: fakeSubmitGrade,
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

  it('does not disable the input field when the disable prop is false', () => {
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

  context('when requests are sent', () => {
    it('shows the loading spinner when submitting a grade', () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      assert.isTrue(wrapper.find(FakeSpinner).exists());
    });

    it('shows the error dialog when the grade request throws an error', () => {
      const wrapper = renderForm();
      fakeSubmitGrade.throws({ errorMessage: '' });
      wrapper.find('button').simulate('click');
      wrapper.update();
      assert.isTrue(wrapper.find(FakeErrorDialog).exists());
    });

    it('sets the `SubmitGradeForm--grade-saved` class when the grade has posted', async () => {
      const wrapper = renderForm();
      fakeSubmitGrade.resolves();
      wrapper.find('button').simulate('click');
      await fakeSubmitGrade.resolves();
      wrapper.update();
      assert.isTrue(
        wrapper.find('input').hasClass('SubmitGradeForm--grade-saved')
      );
    });

    it('closes the spinner after the grade has posted', async () => {
      const wrapper = renderForm();
      wrapper.find('button').simulate('click');
      await fakeSubmitGrade.resolves();
      wrapper.update();
      assert.isFalse(wrapper.find(FakeSpinner).exists());
    });
  });
});
