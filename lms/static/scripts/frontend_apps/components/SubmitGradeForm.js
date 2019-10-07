import { createElement } from 'preact';
import propTypes from 'prop-types';

/**
 * A form with a single input field and submit button for an instructor to
 * save a students grade.
 */

export default function SubmitGradeForm({}) {
  return <form className="SubmitGradeForm" autoComplete="off" />;
}

SubmitGradeForm.propTypes = {
  // Callback to save the grade to the server.
  onSubmitGrade: propTypes.func.isRequired,
  // Disables the the entire form.
  disabled: propTypes.bool,
  // Grade for the current student. (Loaded from the server)
  studentGrade: propTypes.number.isRequired,
  // Renders a quick animation to show it was recently saved.
  gradeSaved: propTypes.bool,
};
