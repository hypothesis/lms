import { LabeledCheckbox, Link } from '@hypothesis/frontend-shared';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import { isAuthorizationError, GroupListEmptyError } from '../errors';
import { apiCall } from '../utils/api';
import { useUniqueId } from '../utils/hooks';

import AuthorizationModal from './AuthorizationModal';
import ErrorModal from './ErrorModal';

/**
 * @typedef {import('../api-types').GroupSet} GroupSet
 */

/**
 * Configuration relating to how students are divided into groups for an
 * assignment.
 *
 * @typedef GroupConfig
 * @prop {boolean} useGroupSet - Whether students are divided into groups based
 *   on a grouping/group set defined in the LMS (the terminology varies depending
 *   on the LMS).
 * @prop {string|null} groupSet - The ID of the grouping to use. This should
 *   be the `id` of a `GroupSet` returned by the LMS backend.
 */

/**
 * Labeled <select> for selecting a group set for an assignment
 *
 * @typedef GroupSelectProps
 * @prop {boolean} busy - A request for groups is currently in flight
 * @prop {GroupSet[]|null} groupSets
 * @prop {(id: string|null) => void} onInput
 * @prop {string|null} selectedGroupSetId
 * @prop {string} productFamily - Which product (canvas, blackboard...) we are running in.
 *
 * @param {GroupSelectProps} props
 */
function GroupSelect({
  busy,
  groupSets,
  onInput,
  selectedGroupSetId,
  productFamily,
}) {
  const selectId = useUniqueId('GroupSetSelector__select');

  return (
    <>
      <GroupSelectHeader htmlFor={selectId} productFamily={productFamily} /> <select
        disabled={busy}
        id={selectId}
        onInput={e =>
          onInput(/** @type {HTMLInputElement} */ (e.target).value || null)
        }
      >
        {busy && <GroupSelectLoadingOption productFamily={productFamily} />}
        {groupSets && (
          <>
            <GroupSelectPromptOption
              productFamily={productFamily}
              groupSelected={selectedGroupSetId === null}
            />
            <hr />
            {groupSets.map(gs => (
              <option
                key={gs.id}
                value={gs.id}
                selected={gs.id === selectedGroupSetId}
                data-testid="groupset-option"
              >
                {gs.name}
              </option>
            ))}
          </>
        )}
      </select>
    </>
  );
}

/**
 * @typedef GroupSelectHeaderProps
 * @prop {string} htmlFor
 * @prop {string} productFamily
 *
 * @param {GroupSelectHeaderProps} props
 */
function GroupSelectHeader({ htmlFor, productFamily }) {
  if (productFamily === 'desire2learn') {
    return <label htmlFor={htmlFor}>Group category: </label>;
  } else {
    return <label htmlFor={htmlFor}>Group set: </label>;
  }
}

/**
 * @typedef GroupSelectLoadingOptionProps
 * @prop {string} productFamily
 *
 * @param {GroupSelectLoadingOptionProps} props
 */

function GroupSelectLoadingOption({ productFamily }) {
  if (productFamily === 'desire2learn') {
    return <option>Fetching group categories…</option>;
  } else {
    return <option>Fetching group sets…</option>;
  }
}

/**
 * @typedef GroupSelectPromptOptionProps
 * @prop {string} productFamily
 * @prop {boolean} groupSelected
 *
 * @param {GroupSelectPromptOptionProps} props
 */

function GroupSelectPromptOption({ productFamily, groupSelected }) {
  const groupSetNaming =
    productFamily === 'desire2learn' ? 'group categories' : 'group set';

  return (
    <option disabled selected={groupSelected}>
      Select {groupSetNaming}
    </option>
  );
}

/**
 * ErrorModal shown when the fetched list of course group sets is empty
 *
 * @param {object} props
 *   @param {() => void} props.onCancel
 *   @param {string} props.productFamily
 */
function NoGroupsError({ onCancel, productFamily }) {
  if (productFamily === 'desire2learn') {
    return (
      <ErrorModal onCancel={onCancel} title="No group categories found">
        <>
          <p>
            Hypothesis relies on group categories to place students into groups,
            but we could not find any available group categories in this course.
          </p>
          <p>
            Please add one or more group category to your course and try again.
            We also have some{' '}
            <Link
              // No KB article for D2L yet
              href="https://web.hypothes.is/?s=group&ht-kb-search=1&lang=%0D%0A%09%09"
              target="_blank"
            >
              help articles about using groups
            </Link>
            .
          </p>
        </>
      </ErrorModal>
    );
  } else if (productFamily === 'canvas') {
    return (
      <ErrorModal onCancel={onCancel} title="No group sets found">
        <>
          <p>
            Hypothesis relies on canvas group sets to place students into
            groups, but we could not find any available group sets in this
            course.
          </p>
          <p>
            Please add one or more group sets to your course and try again. We
            also have a{' '}
            <Link
              href="https://web.hypothes.is/help/using-canvas-groups-to-create-hypothesis-reading-groups/"
              target="_blank"
            >
              help article about using groups in Canvas
            </Link>
            .
          </p>
        </>
      </ErrorModal>
    );
  }
  // TODO BLACKBOARD

  return (
    <ErrorModal onCancel={onCancel} title="No group sets found">
      <>
        <p>
          Hypothesis relies on group sets to place students into groups, but we
          could not find any available group sets in this course.
        </p>
        <p>
          Please add one or more group sets to your course and try again. We
          also have some{' '}
          <Link
            href="https://web.hypothes.is/?s=group&ht-kb-search=1&lang=%0D%0A%09%09"
            target="_blank"
          >
            help articles about using groups
          </Link>
          .
        </p>
      </>
    </ErrorModal>
  );
}

/**
 * @typedef GroupConfigSelectorProps
 * @prop {GroupConfig} groupConfig
 * @prop {(g: GroupConfig) => void} onChangeGroupConfig
 */

/**
 * Component that allows instructors to configure how students are divided into
 * groups for an assignment.
 *
 * In Canvas, there are three possibilities:
 *
 *  1. Use one group for the whole course
 *  2. Use one group per Canvas Section
 *  3. Divide students into multiple groups based on a Canvas Group Set
 *
 * The choice between (1) and (2) is currently part of the configuration of an
 * installation of the Hypothesis LMS app. The choice between (1 or 2) and (3)
 * is done per assignment by the instructor.
 *
 * Other LMSes have similar concepts to a Group Set, although the terminology
 * varies (eg. Moodle has "Groupings").
 *
 * @param {GroupConfigSelectorProps} props
 */
export default function GroupConfigSelector({
  groupConfig,
  onChangeGroupConfig,
}) {
  const [fetchError, setFetchError] = useState(
    /** @type {Error|null} */ (null)
  );

  const [groupSets, setGroupSets] = useState(
    /** @type {GroupSet[]|null} */ (null)
  );

  const {
    api: { authToken },
    product: {
      family: productFamily,
      api: { listGroupSets: listGroupSetsAPI },
    },
  } = useContext(Config);

  const useGroupSet = groupConfig.useGroupSet;
  const groupSet = useGroupSet ? groupConfig.groupSet : null;

  const fetchingGroupSets = !groupSets && !fetchError && useGroupSet;

  // Whether at least one request for a list of groups has completed with a
  // non-null response
  const haveFetchedGroups = groupSets !== null;

  const checkboxId = useUniqueId('GroupSetSelector__enabled');

  const fetchGroupSets = useCallback(async () => {
    setFetchError(null);

    try {
      const groupSets = /** @type {GroupSet[]} */ (
        await apiCall({
          authToken,
          path: listGroupSetsAPI.path,
        })
      );
      if (groupSets && groupSets.length === 0) {
        setFetchError(new GroupListEmptyError());
      } else {
        setGroupSets(groupSets);
      }
    } catch (error) {
      setFetchError(error);
    }
  }, [authToken, listGroupSetsAPI]);

  const onErrorCancel = useCallback(() => {
    // When a user cancels out of an error or authorization modal without
    // resolving the issue, that means we've been unsuccessful in fetching a
    // list of group sets. Update/clear the group configuration, which will
    // result in the checkbox unselecting itself. NB: This logic may be
    // destructive if this component/UI is ever re-used for _editing_ the
    // configuration of an existing assignment.
    setFetchError(null);
    onChangeGroupConfig({
      useGroupSet: false,
      groupSet: null,
    });
  }, [onChangeGroupConfig]);

  const onGroupSelectChange = useCallback(
    /** @param {string|null} groupSetId */
    groupSetId => {
      onChangeGroupConfig({
        useGroupSet,
        groupSet: groupSetId,
      });
    },
    [useGroupSet, onChangeGroupConfig]
  );

  useEffect(() => {
    if (useGroupSet && !haveFetchedGroups) {
      fetchGroupSets();
    }
  }, [fetchGroupSets, useGroupSet, haveFetchedGroups]);

  if (fetchError) {
    if (fetchError instanceof GroupListEmptyError) {
      return (
        <NoGroupsError onCancel={onErrorCancel} productFamily={productFamily} />
      );
    } else if (isAuthorizationError(fetchError)) {
      // TODO
      return (
        <AuthorizationModal
          authURL={/** @type {string} */ (listGroupSetsAPI.authUrl)}
          authToken={authToken}
          onAuthComplete={fetchGroupSets}
          onCancel={onErrorCancel}
        >
          <p>Hypothesis needs your permission to show group sets.</p>
        </AuthorizationModal>
      );
    } else {
      // TODO
      return (
        <ErrorModal
          cancelLabel="Cancel"
          description="There was a problem fetching group sets"
          error={fetchError}
          onCancel={onErrorCancel}
          onRetry={fetchGroupSets}
        />
      );
    }
  }

  return (
    <>
      <LabeledCheckbox
        checked={useGroupSet}
        id={checkboxId}
        // The `name` prop is required by LabeledCheckbox but is unimportant
        // as this field is not actually part of the submitted form.
        name="use_group_set"
        onInput={e =>
          onChangeGroupConfig({
            useGroupSet: /** @type {HTMLInputElement} */ (e.target).checked,
            groupSet: groupSet ?? null,
          })
        }
      >
        This is a group assignment
      </LabeledCheckbox>

      {useGroupSet && (
        <GroupSelect
          busy={fetchingGroupSets}
          groupSets={groupSets}
          selectedGroupSetId={groupSet}
          onInput={onGroupSelectChange}
          productFamily={productFamily}
        />
      )}
    </>
  );
}
