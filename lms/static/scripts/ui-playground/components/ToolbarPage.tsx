import type { ModalProps } from '@hypothesis/frontend-shared/lib/components/feedback/Modal';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  Button,
  CheckIcon,
  EditIcon,
  IconButton,
  Input,
  InputGroup,
  LinkButton,
  Modal,
  Select,
} from '@hypothesis/frontend-shared/lib/next';
import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';
import classnames from 'classnames';
import { useState } from 'preact/hooks';

function ToolbarExample({
  children,
  classes,
  ...modalProps
}: Partial<ModalProps>) {
  const [modalOpen, setModalOpen] = useState(false);
  const closeModal = () => setModalOpen(false);

  if (!modalOpen) {
    return (
      <Button onClick={() => setModalOpen(!modalOpen)} variant="primary">
        Show layout
      </Button>
    );
  } else {
    return (
      <Modal
        title="Toolbar UI"
        {...modalProps}
        classes={classnames('w-[90vw]', classes)}
        width="custom"
        onClose={closeModal}
      >
        <div className="border">{children}</div>
      </Modal>
    );
  }
}

export default function ToolbarPage() {
  return (
    <Library.Page
      title="Instructor Toolbar"
      intro={
        <p>
          These sketches explore some UI possibilities for the Instructor
          Toolbar: adding an edit-assignment link and potentially having a
          collapsible view.
        </p>
      }
    >
      <Library.Section
        title="Full Toolbar layout sketches"
        intro={
          <p>
            Layout examples are shown in modals to provide more available screen
            width. You can resize your browser to see how the layouts adapt to
            different viewports.
          </p>
        }
      >
        <Library.Pattern title="Starting point UI">
          <Library.Demo title="Starting-point UI">
            <ToolbarExample title="Starting-point UI">
              <>
                <header
                  className={classnames(
                    'grid grid-cols-1 items-center gap-y-2 p-2',
                    'lg:grid-cols-3 lg:gap-x-4 lg:px-3'
                  )}
                >
                  <div className="space-y-1">
                    <h1
                      className="text-lg font-semibold leading-none"
                      data-testid="assignment-name"
                    >
                      How four bananas changed the world
                    </h1>
                    <h2
                      className="text-sm font-normal text-color-text-light leading-none"
                      data-testid="course-name"
                    >
                      Fruit and its incredible power
                    </h2>
                  </div>

                  <div
                    className={classnames(
                      'flex flex-col gap-2',
                      'sm:flex-row',
                      'lg:col-span-2 lg:gap-4 ' /* cols 2-3 of 3 */
                    )}
                  >
                    <div className="flex-grow-0 sm:flex-grow">
                      <div
                        className={classnames(
                          // Narrower widths: label above field
                          'flex flex-col gap-1',
                          // Wider widths: label to left of field
                          'xl:flex-row xl:gap-3 xl:items-center'
                        )}
                      >
                        <label
                          className={classnames(
                            'flex-grow font-medium text-sm leading-none',
                            'xl:text-right'
                          )}
                          data-testid="student-selector-label"
                          htmlFor="student-selector"
                        >
                          Student 1 of 5
                        </label>
                        <div>
                          <InputGroup>
                            <IconButton
                              icon={ArrowLeftIcon}
                              title="previous student"
                              variant="dark"
                            />
                            <Select
                              aria-label="Select student"
                              classes="xl:w-80"
                              id="student-selector"
                            >
                              <option key={'all-students'} value={-1}>
                                All Students
                              </option>
                            </Select>
                            <IconButton
                              icon={ArrowRightIcon}
                              title="next student"
                              variant="dark"
                            />
                          </InputGroup>
                        </div>
                      </div>
                    </div>
                    <div className="flex-grow sm:flex-grow-0">
                      <InputGroup classes="flex items-stretch">
                        <Input classes="w-14 h-touch-minimum" disabled />
                        <Button
                          classes="h-touch-minimum opacity-50"
                          disabled
                          icon={CheckIcon}
                        >
                          Submit Grade
                        </Button>
                      </InputGroup>
                    </div>
                  </div>
                </header>
              </>
            </ToolbarExample>
          </Library.Demo>
        </Library.Pattern>
      </Library.Section>
      <Library.Section title="Assignment edit button">
        <Library.Pattern title="Using a simple link-style button">
          <Library.Demo title="Simple button-link">
            <div className="space-y-1">
              <div className="flex gap-x-2 items-center">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  How four bananas changed the world
                </h1>
                <LinkButton classes="text-xs" underline="always">
                  Edit
                </LinkButton>
              </div>
              <h2
                className="text-sm font-normal text-color-text-light leading-none"
                data-testid="course-name"
              >
                Fruit and its incredible power
              </h2>
            </div>
          </Library.Demo>

          <Library.Demo title="Simple button-link: Short assignment title">
            <div className="space-y-1">
              <div className="flex gap-x-2 items-center">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  Short title
                </h1>
                <LinkButton classes="text-xs" underline="always">
                  Edit
                </LinkButton>
              </div>
              <h2
                className="text-sm font-normal text-color-text-light leading-none"
                data-testid="course-name"
              >
                Long course name here
              </h2>
            </div>
          </Library.Demo>
          <Library.Demo title="Simple button-link on second line">
            <div className="space-y-1">
              <div className="flex gap-x-2">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  How four bananas changed the world
                </h1>
              </div>
              <LinkButton underline="always">Edit assignment</LinkButton>
            </div>
          </Library.Demo>
          <Library.Demo title="One-line simple button-link">
            <div className="space-y-1">
              <div className="flex gap-x-2 items-center">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  How four bananas changed the world
                </h1>
                <LinkButton classes="text-xs" underline="always">
                  Edit
                </LinkButton>
              </div>
            </div>
          </Library.Demo>
        </Library.Pattern>

        <Library.Pattern title="Using a button">
          <Library.Demo title="Left-side edit button">
            <div className="flex gap-x-2">
              <Button>Edit</Button>
              <div className="space-y-1">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  How four bananas changed the world
                </h1>
                <h2
                  className="text-sm font-normal text-color-text-light leading-none"
                  data-testid="course-name"
                >
                  Fruit and its incredible power
                </h2>
              </div>
            </div>
          </Library.Demo>
          <Library.Demo title="Left-side edit button with icon">
            <div className="flex gap-x-3">
              <Button icon={EditIcon}>Edit</Button>
              <div className="space-y-1">
                <h1
                  className="text-lg font-semibold leading-none"
                  data-testid="assignment-name"
                >
                  How four bananas changed the world
                </h1>
                <h2
                  className="text-sm font-normal text-color-text-light leading-none"
                  data-testid="course-name"
                >
                  Fruit and its incredible power
                </h2>
              </div>
            </div>
          </Library.Demo>
        </Library.Pattern>
      </Library.Section>
    </Library.Page>
  );
}
