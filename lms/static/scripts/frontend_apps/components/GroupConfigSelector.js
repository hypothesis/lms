import { LabeledCheckbox } from '@hypothesis/frontend-shared';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import { isAuthorizationError } from '../errors';
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
    filePicker: { blackboard, canvas },
  } = useContext(Config);

  const useGroupSet = groupConfig.useGroupSet;
  const haveFetchedGroups = groupSets !== null;

  const groupSet = useGroupSet ? groupConfig.groupSet : null;
  const fetchingGroupSets = !groupSets && !fetchError && useGroupSet;

  const listGroupSetsAPI = canvas?.listGroupSets ?? blackboard?.listGroupSets;

  const checkboxID = useUniqueId('GroupSetSelector__enabled');
  const selectID = useUniqueId('GroupSetSelector__select');

  const fetchGroupSets = useCallback(async () => {
    setFetchError(null);

    try {
      const groupSets = /** @type {GroupSet[]} */ (
        await apiCall({
          authToken,
          path: listGroupSetsAPI.path,
        })
      );
      setGroupSets(groupSets);
    } catch (error) {
      setFetchError(error);
    }
  }, [authToken, listGroupSetsAPI]);

  const onErrorCancel = () => {
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
  };

  useEffect(() => {
    if (useGroupSet && !haveFetchedGroups) {
      fetchGroupSets();
    }
  }, [fetchGroupSets, useGroupSet, haveFetchedGroups]);

  return (
    <>
      <div>
        <LabeledCheckbox
          checked={useGroupSet}
          id={checkboxID}
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
      </div>
      {useGroupSet && (
        <div>
          {fetchError && isAuthorizationError(fetchError) && (
            // Currently all fetch errors are handled by attempting to re-authorize
            // and then re-fetch group sets.
            <AuthorizationModal
              authURL={/** @type {string} */ (listGroupSetsAPI.authUrl)}
              authToken={authToken}
              onAuthComplete={fetchGroupSets}
              onCancel={onErrorCancel}
            >
              <p>Hypothesis needs your permission to show group sets.</p>
            </AuthorizationModal>
          )}
          {fetchError && !isAuthorizationError(fetchError) && (
            <ErrorModal
              description="There was a problem fetching group sets"
              error={fetchError}
              onCancel={onErrorCancel}
              onRetry={fetchGroupSets}
            />
          )}
          {!fetchError && (
            <>
              <label htmlFor={selectID}>Group set: </label>
              <select
                disabled={fetchingGroupSets}
                id={selectID}
                onInput={e =>
                  onChangeGroupConfig({
                    useGroupSet,
                    groupSet:
                      /** @type {HTMLInputElement} */ (e.target).value || null,
                  })
                }
              >
                {fetchingGroupSets && <option>Fetching group sets…</option>}
                {groupSets && (
                  <>
                    <option disabled selected={groupSet === null}>
                      Select group set
                    </option>
                    <hr />
                    {groupSets.map(gs => (
                      <option
                        key={gs.id}
                        value={gs.id}
                        selected={gs.id === groupSet}
                        data-testid="groupset-option"
                      >
                        {gs.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </>
          )}
        </div>
      )}
    </>
  );
}
