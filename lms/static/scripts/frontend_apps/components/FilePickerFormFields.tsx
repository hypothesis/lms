import type { Content } from '../utils/content-item';

export type FilePickerFormFieldsProps = {
  /** Content for the assignment. */
  content: Content;

  /**
   * Form field values provided by the backend that should be rendered as
   * hidden input fields.
   */
  formFields: Record<string, string>;

  groupSet: string | null;
};

/**
 * Render the hidden form fields in the file picker form containing information
 * about the selected assignment.
 *
 * This form may be used in two different scenarios:
 *
 *  - A "Content Item Selection" form when configuring an assignment. In this
 *    case the form will look like "Section 3.2, Example Response" in
 *    https://www.imsglobal.org/specs/lticiv1p0/specification
 *  - When an assignment without any content configuration is launched.
 *    See the `configure_assignment` view.
 */
export default function FilePickerFormFields({
  content,
  formFields,
  groupSet,
}: FilePickerFormFieldsProps) {
  return (
    <>
      {Object.entries(formFields).map(([field, value]) => (
        <input key={field} type="hidden" name={field} value={value} />
      ))}
      {groupSet && <input type="hidden" name="group_set" value={groupSet} />}
      {content.type === 'url' && (
        // Set the `document_url` form field which is used by the `configure_assignment`
        // view. Used in LMSes where assignments are configured on first launch.
        <input name="document_url" type="hidden" value={content.url} />
      )}
    </>
  );
}