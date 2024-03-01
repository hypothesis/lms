import { Checkbox, Link, Select } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useEffect, useState } from 'preact/hooks';

import type { GroupSet } from '../api-types';
import { useConfig } from '../config';
import { isAuthorizationError, GroupListEmptyError } from '../errors';
import { apiCall } from '../utils/api';
import { useUniqueId } from '../utils/hooks';
import AuthorizationModal from './AuthorizationModal';
import ErrorModal from './ErrorModal';

/**
 * Configuration relating to how students are divided into groups for an
 * assignment.
 */
export type GroupConfig = {
  /**
   * Whether students are divided into groups based on a grouping/group set
   * defined in the LMS (the terminology varies depending on the LMS).
   */
  useGroupSet: boolean;

  /**
   * The ID of the grouping to use. This should be the `id` of a `GroupSet`
   * returned by the LMS backend.
   */
  groupSet: string | null;
};

type GroupSelectProps = {
  /** A request for groups is currently in flight */
  loading: boolean;
  groupSets: GroupSet[] | null;
  onInput: (id: string | null) => void;
  selectedGroupSetId: string | null;
};

/**
 * Labeled <select> for selecting a group set for an assignment
 */
function GroupSelect({
  loading,
  groupSets,
  onInput,
  selectedGroupSetId,
}: GroupSelectProps) {
  const selectId = useUniqueId('GroupSetSelector__select');

  return (
    <div
      className={classnames(
        // Style a slightly-recessed "well" for these controls
        'bg-slate-0 p-4 rounded shadow-inner border',
      )}
    >
      <label
        htmlFor={selectId}
        className="text-xs uppercase text-slate-7 font-medium"
      >
        Group set
      </label>
      <Select
        disabled={loading}
        id={selectId}
        onInput={(e: Event) =>
          onInput((e.target as HTMLSelectElement | null)?.value || null)
        }
      >
        {loading && <option>Fetching group sets…</option>}
        {groupSets && (
          <>
            <option disabled selected={selectedGroupSetId === null}>
              Select group set
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
      </Select>
    </div>
  );
}

/**
 * ErrorModal shown when the fetched list of course group sets is empty
 */
function NoGroupsError({ onCancel }: { onCancel: () => void }) {
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
            underline="none"
          >
            help articles about using groups
          </Link>
          .
        </p>
      </>
    </ErrorModal>
  );
}

export type GroupConfigSelectorProps = {
  groupConfig: GroupConfig;
  onChangeGroupConfig: (g: GroupConfig) => void;
};

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
 */
export default function GroupConfigSelector({
  groupConfig,
  onChangeGroupConfig,
}: GroupConfigSelectorProps) {
  const [fetchError, setFetchError] = useState<Error | null>(null);
  const [groupSets, setGroupSets] = useState<GroupSet[] | null>(null);

  const {
    api: { authToken },
    product: {
      api: { listGroupSets: listGroupSetsAPI },
    },
  } = useConfig(['api']);

  const useGroupSet = groupConfig.useGroupSet;
  const groupSet = useGroupSet ? groupConfig.groupSet : null;

  const fetchingGroupSets = !groupSets && !fetchError && useGroupSet;

  // Whether at least one request for a list of groups has completed with a
  // non-null response
  const haveFetchedGroups = groupSets !== null;

  const fetchGroupSets = useCallback(async () => {
    setFetchError(null);

    try {
      const groupSets: GroupSet[] = await apiCall({
        authToken,
        path: listGroupSetsAPI.path,
        data: listGroupSetsAPI.data,
      });
      if (groupSets.length === 0) {
        setFetchError(new GroupListEmptyError());
      } else {
        // FIXME - Workaround a backend issue where group set IDs are returned
        // as numbers instead of strings in D2L. The backend should be fixed
        // to always return strings.
        groupSets.forEach(gs => {
          gs.id = String(gs.id);
        });

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
    (groupSetId: string | null) => {
      onChangeGroupConfig({
        useGroupSet,
        groupSet: groupSetId,
      });
    },
    [useGroupSet, onChangeGroupConfig],
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
          authURL={listGroupSetsAPI.authUrl!}
          authToken={authToken}
          onAuthComplete={fetchGroupSets}
          onCancel={onErrorCancel}
        >
          <p>Hypothesis needs your permission to show group sets.</p>
        </AuthorizationModal>
      );
    } else {
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
    <div className="space-y-3">
      <Checkbox
        checked={useGroupSet}
        onInput={(e: Event) =>
          onChangeGroupConfig({
            useGroupSet: (e.target as HTMLInputElement).checked,
            groupSet: groupSet ?? null,
          })
        }
      >
        This is a group assignment
      </Checkbox>
      {useGroupSet && (
        <GroupSelect
          loading={fetchingGroupSets}
          groupSets={groupSets}
          selectedGroupSetId={groupSet}
          onInput={onGroupSelectChange}
        />
      )}
    </div>
  );
}
