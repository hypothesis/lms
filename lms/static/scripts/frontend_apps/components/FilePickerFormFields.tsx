import type { AutoGradingConfig } from '../api-types';
import type { Content } from '../utils/content-item';

export type FilePickerFormFieldsProps = {
  /** Content for the assignment. */
  content: Content;

  /**
   * Form field values provided by the backend that should be rendered as
   * hidden input fields.
   * These are used while using our own assignment configuration flow
   * ie. while not using deep linking.
   */
  formFields: Record<string, string>;

  /**
   * ID of the group set or category selected for this assignment, or `null`
   * if group sets have been disabled.
   */
  groupSet: string | null;

  /** Assignment title chosen by the user, if supported by the current LMS. */
  title: string | null;

  /**
   * Auto-grading configuration for assignments where it is enabled: one config
   * for a single grade, one per grading phase for paced grades.
   */
  autoGradingConfig: AutoGradingConfig | AutoGradingConfig[] | null;

  /** Whether this is a "Hide & Reveal" assignment. */
  checkpointEnabled: boolean;

  /** Due date as a UTC ISO string, or `null` when not set. */
  dueDate: string | null;
};

/**
 * Render the hidden form fields in the file picker form containing information
 * about the selected assignment.
 *
 * Used when an assignment without any content configuration is launched.
 */
export default function FilePickerFormFields({
  title,
  content,
  formFields,
  groupSet,
  autoGradingConfig,
  checkpointEnabled,
  dueDate,
}: FilePickerFormFieldsProps) {
  return (
    <>
      {Object.entries(formFields).map(([field, value]) => (
        <input key={field} type="hidden" name={field} value={value} />
      ))}
      <input type="hidden" name="group_set" value={groupSet ?? ''} />
      {content.type === 'url' && (
        // Set the `document_url` form field which is used by the `configure_assignment`
        // view. Used in LMSes where assignments are configured on first launch.
        <input name="document_url" type="hidden" value={content.url} />
      )}
      {title !== null && <input type="hidden" name="title" value={title} />}
      {autoGradingConfig && (
        <input
          type="hidden"
          name="auto_grading_config"
          value={JSON.stringify(autoGradingConfig)}
        />
      )}
      {checkpointEnabled && (
        <input type="hidden" name="checkpoint_enabled" value="true" />
      )}
      {/* Emitted on its own rather than alongside `checkpoint_enabled`. The
          caller decides whether a date applies -- and only ever passes one for
          a checkpoint assignment -- so a second check here would be either
          redundant or, once other kinds of assignment carry a date, a silent
          way to drop it. The deep-linking path sends `due_date` on the same
          terms: whatever it was handed. */}
      {dueDate && <input type="hidden" name="due_date" value={dueDate} />}
    </>
  );
}
