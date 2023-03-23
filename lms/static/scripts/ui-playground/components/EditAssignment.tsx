import {
  ArrowLeftIcon,
  Button,
  Card,
  CardActions,
  CardContent,
  Checkbox,
  LinkButton,
} from '@hypothesis/frontend-shared/lib/next';
import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useState } from 'preact/hooks';

function PickerCard({
  children,
  headerContent,
}: {
  children: ComponentChildren;
  headerContent?: ComponentChildren;
}) {
  return (
    <div
      className={classnames(
        'bg-grey-1 w-full h-full',
        // "Real" implementation uses p-2 but this gives more space in demos here
        'p-2'
      )}
    >
      {headerContent}
      <div
        className={classnames(
          'w-[640px] max-w-[80vw]',
          'flex flex-col min-h-0 h-full',
          'mx-auto'
        )}
      >
        <Card classes={classnames('flex flex-col min-h-0')}>{children}</Card>
      </div>
    </div>
  );
}

function PickerCardHeader({ children }: { children: ComponentChildren }) {
  return (
    <div className="bg-slate-0 px-3 py-2 border-b border-slate-5">
      <h1 className="text-xl text-slate-7 font-normal">{children}</h1>
    </div>
  );
}

function PickerCardContent({ children }: { children: ComponentChildren }) {
  return (
    <CardContent size="lg">
      <div className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3">
        {children}
      </div>
    </CardContent>
  );
}

function PickerCardRow({
  children,
  label = '',
}: {
  children: ComponentChildren;
  label?: string;
}) {
  return (
    <>
      <div className="text-end self-center">
        <span className="font-medium text-sm leading-none text-slate-7">
          {label}
        </span>
      </div>
      <div className="space-y-3">{children}</div>
    </>
  );
}

function ReselectContentExample() {
  const [reselectActive, setReselectActive] = useState(false);
  return (
    <PickerCard
      headerContent={
        <div className="flex gap-x-1 mx-4 my-2">
          <LinkButton classes="gap-x-1" underline="always">
            <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
            Back to Assignment
          </LinkButton>
        </div>
      }
    >
      <PickerCardHeader>Assignment details</PickerCardHeader>
      <PickerCardContent>
        <PickerCardRow label="Assignment content">
          <div className="flex gap-x-2 items-center">
            <div>
              <i>https://www.example.com</i>
            </div>
            <div className="border-r">&nbsp;</div>
            {reselectActive ? (
              <LinkButton
                classes="text-xs"
                underline="always"
                onClick={() => setReselectActive(!reselectActive)}
              >
                Cancel changes
              </LinkButton>
            ) : (
              <LinkButton
                classes="text-xs"
                underline="always"
                onClick={() => setReselectActive(!reselectActive)}
              >
                Change
              </LinkButton>
            )}
          </div>
        </PickerCardRow>
        {reselectActive && (
          <PickerCardRow>
            <div
              className={classnames(
                // Style a slightly-recessed "well" for these controls
                'bg-slate-0 p-4 rounded shadow-inner border space-y-2'
              )}
            >
              <p>
                Select updated content for your assignment from one of the
                following sources:
              </p>
              <div className="flex">
                <div className="flex flex-col space-y-1">
                  <Button variant="primary">
                    Enter URL of web page or PDF
                  </Button>
                  <Button variant="primary">Select PDF from Canvas</Button>
                  <Button variant="primary">
                    Select PDF from Google Drive
                  </Button>
                  <Button variant="primary">Select JSTOR article</Button>
                  <Button variant="primary">Select PDF from OneDrive</Button>
                </div>
                <div className="grow" />
              </div>
            </div>
          </PickerCardRow>
        )}
        <div className="col-span-2 border-b" />
        <PickerCardRow label="Group assignment">
          <Checkbox>This is a group assignment</Checkbox>
        </PickerCardRow>
      </PickerCardContent>
      <CardContent>
        <CardActions>
          <Button variant="primary">Save</Button>
        </CardActions>
      </CardContent>
    </PickerCard>
  );
}

export default function EditAssignmentPage() {
  return (
    <Library.Page
      title="Edit Assignment UI"
      intro={
        <>
          <p>
            This page documents existing design and UI for configuring
            assignments and proposes some options for UI enhancement.
          </p>
          <p>
            The assignment-configuration UI was originally designed under the
            assumption that it would be followed linearly for an assignment that
            had not yet been configured. With the introduction of support to
            edit existing assignment configuration, the UI needs to be
            revisited.
          </p>
        </>
      }
    >
      <Library.Section
        title="Configure assignment workflow"
        intro={
          <p>
            This UI workflow is what an instructor user sees when they configure
            an assignment that has not been configured before and represents the
            original intent of the UI.
          </p>
        }
      >
        <Library.Pattern title="Original (Existing) UI">
          <Library.Example title="Step 1: Select assignment content">
            <Library.Demo>
              <PickerCard>
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <p>
                      You can select content for your assignment from one of the
                      following sources:
                    </p>
                  </PickerCardRow>
                  <PickerCardRow>
                    <div className="flex">
                      <div className="flex flex-col space-y-1">
                        <Button variant="primary">
                          Enter URL of web page or PDF
                        </Button>
                        <Button variant="primary">
                          Select PDF from Canvas
                        </Button>
                        <Button variant="primary">
                          Select PDF from Google Drive
                        </Button>
                        <Button variant="primary">Select JSTOR article</Button>
                        <Button variant="primary">
                          Select PDF from OneDrive
                        </Button>
                      </div>
                      <div className="grow" />
                    </div>
                  </PickerCardRow>
                </PickerCardContent>
              </PickerCard>
            </Library.Demo>
          </Library.Example>

          <Library.Example title="Step 2: Groups configuration">
            <p>
              Once content is selected, this second view is presented for groups
              configuration.
            </p>
            <p>
              <em>NB</em>: This screen is not shown if groups are not
              enabled/available.
            </p>
            <Library.Demo>
              <PickerCard>
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <div className="flex gap-x-2 items-center">
                      <i>https://www.example.com</i>
                    </div>
                  </PickerCardRow>
                  <div className="col-span-2 border-b" />
                  <PickerCardRow label="Group assignment">
                    <Checkbox>This is a group assignment</Checkbox>
                  </PickerCardRow>
                </PickerCardContent>
                <CardContent>
                  <CardActions>
                    <Button variant="primary">Continue</Button>
                  </CardActions>
                </CardContent>
              </PickerCard>
            </Library.Demo>
          </Library.Example>
        </Library.Pattern>
      </Library.Section>
      <Library.Section
        title="Edit assignment workflow"
        intro={
          <p>
            This UI workflow is what an instructor user would see when they edit
            a previously-configured {"assignment's"} settings by clicking on the{' '}
            {'"Edit"'} button in the {'"Instructor Toolbar"'}.
          </p>
        }
      >
        <Library.Pattern title="Edit assignment: initial view">
          <p>Actions available in this view:</p>
          <ul>
            <li>
              Commit (save) assignment settings including any updated group
              settings.
            </li>
            <li>Exit (cancel) the edit flow.</li>
            <li>
              Elect to change the content for the assignment. This takes the
              user to the {'"Edit assignment: re-select content view"'}.
            </li>
          </ul>
          <Library.Example title="Edit-assignment, initial view: sketches">
            <Library.Demo>
              <PickerCard>
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <div className="flex gap-x-2 items-center">
                      <div>
                        <i>https://www.example.com</i>
                      </div>
                      <div className="border-r">&nbsp;</div>
                      <LinkButton classes="text-xs" underline="always">
                        Change
                      </LinkButton>
                    </div>
                  </PickerCardRow>
                  <div className="col-span-2 border-b" />
                  <PickerCardRow label="Group assignment">
                    <Checkbox>This is a group assignment</Checkbox>
                  </PickerCardRow>
                </PickerCardContent>
                <CardContent>
                  <CardActions>
                    <Button>Cancel</Button>
                    <Button variant="primary">Save settings</Button>
                  </CardActions>
                </CardContent>
              </PickerCard>
            </Library.Demo>

            <Library.Demo>
              <PickerCard
                headerContent={
                  <div className="flex gap-x-1 mx-4 my-2">
                    <LinkButton classes="gap-x-1" underline="always">
                      <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
                      Back to Assignment
                    </LinkButton>
                  </div>
                }
              >
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <div className="flex gap-x-2 items-center">
                      <div>
                        <i>https://www.example.com</i>
                      </div>
                      <div className="border-r">&nbsp;</div>
                      <LinkButton classes="text-xs" underline="always">
                        Change
                      </LinkButton>
                    </div>
                  </PickerCardRow>
                  <div className="col-span-2 border-b" />
                  <PickerCardRow label="Group assignment">
                    <Checkbox>This is a group assignment</Checkbox>
                  </PickerCardRow>
                </PickerCardContent>
                <CardContent>
                  <CardActions>
                    <Button>Cancel</Button>
                    <Button variant="primary">Save</Button>
                  </CardActions>
                </CardContent>
              </PickerCard>
            </Library.Demo>

            <Library.Demo>
              <PickerCard
                headerContent={
                  <div className="flex gap-x-1 mx-4 my-2">
                    <LinkButton classes="gap-x-1" underline="always">
                      <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
                      Back to Assignment
                    </LinkButton>
                  </div>
                }
              >
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <div className="flex gap-x-2 items-center">
                      <div>
                        <i>PDF file in Canvas</i>
                      </div>
                      <Button size="sm">Change</Button>
                    </div>
                  </PickerCardRow>
                  <div className="col-span-2 border-b" />
                  <PickerCardRow label="Group assignment">
                    <Checkbox>This is a group assignment</Checkbox>
                  </PickerCardRow>
                </PickerCardContent>
                <CardContent>
                  <CardActions>
                    <Button variant="primary">Save</Button>
                  </CardActions>
                </CardContent>
              </PickerCard>
            </Library.Demo>

            <Library.Demo>
              <PickerCard
                headerContent={
                  <div className="flex gap-x-1 mx-4 my-2">
                    <LinkButton classes="gap-x-1" underline="always">
                      <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
                      Back to Assignment
                    </LinkButton>
                  </div>
                }
              >
                <PickerCardHeader>Assignment details</PickerCardHeader>
                <PickerCardContent>
                  <PickerCardRow label="Assignment content">
                    <div className="flex gap-x-2 items-center">
                      <div>
                        <i>https://www.example.com</i>
                      </div>
                      <div className="border-r">&nbsp;</div>
                      <LinkButton classes="text-xs" underline="always">
                        Change
                      </LinkButton>
                    </div>
                  </PickerCardRow>
                  <div className="col-span-2 border-b" />
                </PickerCardContent>
                <CardContent>
                  <CardActions>
                    <Button variant="primary">Save settings</Button>
                  </CardActions>
                </CardContent>
              </PickerCard>
            </Library.Demo>
          </Library.Example>
        </Library.Pattern>

        <Library.Pattern title="Edit assignment: interactive view sketch">
          <Library.Example title="Edit-assignment with re-selection of content">
            <p>
              This example demonstrates possible UI behavior when user clicks{' '}
              {'"Change"'} button.
            </p>
            <p>
              This variant keeps the user in the same screen for the entire edit
              flow.
            </p>
            <Library.Demo>
              <ReselectContentExample />
            </Library.Demo>
          </Library.Example>
        </Library.Pattern>
      </Library.Section>
    </Library.Page>
  );
}
