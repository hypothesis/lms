export type HiddenFormFieldsProps = {
  /**
   * Form field values to be rendered as hidden inputs.
   */
  fields: Record<string, string>;
};

/**
 * Render fields as hidden form fields.
 */
export default function HiddenFormFields({ fields }: HiddenFormFieldsProps) {
  return (
    <>
      {Object.entries(fields).map(([field, value]) => (
        <input key={field} type="hidden" name={field} value={value} />
      ))}
    </>
  );
}
