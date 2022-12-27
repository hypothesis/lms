import { LabeledCheckbox, Link } from '@hypothesis/frontend-shared';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import { isAuthorizationError, GroupListEmptyError } from '../errors';
import { apiCall } from '../utils/api';
import { useUniqueId } from '../utils/hooks';

import AuthorizationModal from './AuthorizationModal';
import ErrorModal from './ErrorModal';

const messages = {
  groupSetLabel: 'Group set: ',
  groupSetLabel_desire2learn: 'Group category: ',
  noGroupSets: 'No group sets found',
  noGroupSets_desire2learn: 'No group categories found',
  needPermissionToShowGroupSets:
    'Hypothesis needs your permission to show group sets.',
  needPermissionToShowGroupSets_desire2learn:
    'Hypothesis needs your permission to show group categories.',
  problemFetchingGroupSets: 'There was a problem fetching group sets',
  problemFetchingGroupSets_desire2learn:
    'There was a problem fetching group categories',
  pleaseAddGroupSets:
    'Please add one or more group sets to your course and try again.',
  pleaseAddGroupSets_desire2learn:
    'Please add one or more group categories to your course and try again.',
  reliesGroupSetsCantFind:
    'Hypothesis relies on group sets to place students into groups, but we could not find any available group sets in this course.',
  reliesGroupSetsCantFind_desire2learn:
    'Hypothesis relies on group categories to place students into groups, but we could not find any available group categories in this course.',
  fetchingGroupSets: 'Fetching group sets…',
  fetchingGroupSets_desire2learn: 'Fetching group categories…',
  selectGroupSet: 'Select group set',
  selectGroupSet_desire2learn: 'Select group category',
};

/**
 * Poor man's gettext. Not used for i18n but to account for nomenclature differences across LMS
 *
 * @param {string} id
 * @param {string|null} productFamily
 * @returns {string}
 */
const message = (id, productFamily) =>
  messages[id + '_' + productFamily] ?? messages[id];

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
 *
 * @param {GroupSelectProps} props
 */
function GroupSelect({ busy, groupSets, onInput, selectedGroupSetId }) {
  const selectId = useUniqueId('GroupSetSelector__select');
  const {
    product: { family: productFamily },
  } = useContext(Config);

  return (
    <>
      <label htmlFor={selectId}>
        {message('groupSetLabel', productFamily)}
      </label>
      <select
        disabled={busy}
        id={selectId}
        onInput={e =>
          onInput(/** @type {HTMLInputElement} */ (e.target).value || null)
        }
      >
        {busy && <option>{message('fetchingGroupSets', productFamily)}</option>}
        {groupSets && (
          <>
            <option disabled selected={selectedGroupSetId === null}>
              {message('selectGroupSet', productFamily)}
            </option>
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
 * ErrorModal shown when the fetched list of course group sets is empty
 *
 * @param {object} props
 *   @param {() => void} props.onCancel
 */
function NoGroupsError({ onCancel }) {
  const {
    product: { family: productFamily },
  } = useContext(Config);

  return (
    <ErrorModal
      onCancel={onCancel}
      title={message('noGroupSets', productFamily)}
    >
      <>
        <p>{message('reliesGroupSetsCantFind', productFamily)}</p>
        <p>
          {message('pleaseAddGroupSets', productFamily)}
          We also have some{' '}
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
      return <NoGroupsError onCancel={onErrorCancel} />;
    } else if (isAuthorizationError(fetchError)) {
      return (
        <AuthorizationModal
          authURL={/** @type {string} */ (listGroupSetsAPI.authUrl)}
          authToken={authToken}
          onAuthComplete={fetchGroupSets}
          onCancel={onErrorCancel}
        >
          <p>{message('needPermissionToShowGroupSets', productFamily)}</p>
        </AuthorizationModal>
      );
    } else {
      return (
        <ErrorModal
          cancelLabel="Cancel"
          description={message('problemFetchingGroupSets', productFamily)}
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
        />
      )}
    </>
  );
}
