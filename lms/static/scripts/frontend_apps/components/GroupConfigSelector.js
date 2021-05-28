import { LabeledCheckbox } from '@hypothesis/frontend-shared';
import { Fragment, createElement } from 'preact';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import { apiCall } from '../utils/api';
import { useUniqueId } from '../utils/hooks';

import AuthButton from './AuthButton';

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
  const [groupSets, setGroupSets] = useState(
    /** @type {GroupSet[]|null} */ (null)
  );

  const [fetchError, setFetchError] = useState(
    /** @type {Error|null} */ (null)
  );

  const {
    api: { authToken },
    filePicker: {
      canvas: { listGroupSets: listGroupSetsAPI },
    },
  } = useContext(Config);

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
    } catch (err) {
      setFetchError(err);
    }
  }, [authToken, listGroupSetsAPI]);

  const useGroupSet = groupConfig.useGroupSet;
  const haveFetchedGroups = groupSets !== null;

  useEffect(() => {
    if (useGroupSet && !haveFetchedGroups) {
      fetchGroupSets();
    }
  }, [fetchGroupSets, useGroupSet, haveFetchedGroups]);

  const checkboxID = useUniqueId('GroupSetSelector__enabled');
  const selectID = useUniqueId('GroupSetSelector__select');

  const groupSet = groupConfig.useGroupSet ? groupConfig.groupSet : null;
  const fetchingGroupSets = !groupSets && !fetchError && useGroupSet;

  return (
    <Fragment>
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
      {fetchError && useGroupSet && (
        // Currently all fetch errors are handled by attempting to re-authorize
        // and then re-fetch group sets.
        <Fragment>
          <p>Canvas needs your permission to fetch group sets</p>
          <AuthButton
            authURL={/** @type {string} */ (listGroupSetsAPI.authUrl)}
            authToken={authToken}
            onAuthComplete={fetchGroupSets}
          />
        </Fragment>
      )}
      {!fetchError && useGroupSet && (
        <div>
          <label htmlFor={selectID}>Group set:</label>
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
              <Fragment>
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
              </Fragment>
            )}
          </select>
        </div>
      )}
    </Fragment>
  );
}
