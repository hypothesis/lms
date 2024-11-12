import { Select } from '@hypothesis/frontend-shared';
import {
  mockImportedComponents,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import GroupConfigSelector, { $imports } from '../GroupConfigSelector';

describe('GroupConfigSelector', () => {
  const authURL = 'https://testlms.hypothes.is/authorize';
  const groupSetsAPIRequest = {
    authToken: 'valid-token',
    path: '/api/group-sets',
    data: { some: 'data' },
  };

  let fakeAPICall;
  let fakeConfig;
  let fakeGroupSets;
  let fakeIsAuthorizationError;
  let wrappers;
  let containers;

  beforeEach(() => {
    fakeGroupSets = [
      {
        id: 'groupSet1',
        name: 'Group Set 1',
      },
      {
        id: 'groupSet2',
        name: 'Group Set 2',
      },
    ];
    wrappers = [];
    containers = [];

    fakeAPICall = sinon.stub();
    fakeAPICall.withArgs(groupSetsAPIRequest).resolves(fakeGroupSets);
    fakeConfig = {
      api: { authToken: groupSetsAPIRequest.authToken },
      product: {
        api: {
          listGroupSets: {
            authUrl: authURL,
            path: groupSetsAPIRequest.path,
            data: groupSetsAPIRequest.data,
          },
        },
      },
    };
    fakeIsAuthorizationError = sinon.stub();

    $imports.$mock(mockImportedComponents());

    // Avoid mocking shared components so we can treat them just like native
    // form controls. We might want to do this for other tests in future.
    $imports.$restore({
      '@hypothesis/frontend-shared': true,
    });

    $imports.$mock({
      '../errors': { isAuthorizationError: fakeIsAuthorizationError },
      '../utils/api': { apiCall: fakeAPICall },
    });
  });

  afterEach(() => {
    $imports.$restore();
    wrappers.forEach(w => w.unmount());
    containers.forEach(c => c.remove());
  });

  // Helper that simulates GroupConfigSelector's containing component.
  function Container(props) {
    const noop = () => {};
    return (
      <Config.Provider value={fakeConfig}>
        <GroupConfigSelector
          groupConfig={{ useGroupSet: false, groupSet: null }}
          onChangeGroupConfig={noop}
          {...props}
        />
      </Config.Provider>
    );
  }

  function createComponent(props = {}) {
    const container = document.createElement('div');
    containers.push(container);
    document.body.appendChild(container);

    const wrapper = mount(<Container {...props} />, { attachTo: container });
    wrappers.push(wrapper);

    return wrapper;
  }

  function toggleCheckbox(wrapper) {
    const checkbox = wrapper.find('input[type="checkbox"]');
    checkbox.getDOMNode().click();
    checkbox.simulate('input');
  }

  async function getOpenSelect(wrapper) {
    const select = wrapper.find('Select');
    select.find('button').simulate('click');
    const options = await waitForElement(wrapper, Select.Option);

    return { select, options };
  }

  [
    [{ useGroupSet: false, groupSet: null }, false],
    [{ useGroupSet: true, groupSet: null }, true],
  ].forEach(([groupConfig, shouldBeChecked], index) => {
    it(`sets checkbox state to reflect \`useGroupSet\` state (${index})`, () => {
      const wrapper = createComponent({ groupConfig });
      assert.equal(wrapper.find('Checkbox').prop('checked'), shouldBeChecked);
    });
  });

  it('invokes `onChangeGroupConfig` callback when checkbox is checked', () => {
    const onChangeGroupConfig = sinon.stub();
    const wrapper = createComponent({ onChangeGroupConfig });

    toggleCheckbox(wrapper);
    assert.calledWith(onChangeGroupConfig, {
      useGroupSet: true,
      groupSet: null,
    });

    onChangeGroupConfig.resetHistory();
    toggleCheckbox(wrapper);
    assert.calledWith(onChangeGroupConfig, {
      useGroupSet: false,
      groupSet: null,
    });
  });

  it('fetches available group sets when checkbox is checked', async () => {
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupConfig: null },
    });

    // While groups are being fetched, the `<Select>` should be visible but
    // disabled, and display a fetching status.
    const { select: groupSetSelect, options } = await getOpenSelect(wrapper);

    assert.isTrue(groupSetSelect.exists());
    assert.isTrue(groupSetSelect.prop('disabled'));
    assert.equal(groupSetSelect.prop('buttonContent'), 'Fetching group sets…');
    assert.equal(options.length, fakeGroupSets.length);

    fakeGroupSets.forEach((gs, i) => {
      assert.equal(options.at(i).text(), gs.name);
      assert.equal(options.at(i).prop('value'), gs);
    });
  });

  it('invokes `onChangeGroupConfig` callback when a group set is selected', async () => {
    const onChangeGroupConfig = sinon.stub();
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
      onChangeGroupConfig,
    });

    const { select, options } = await getOpenSelect(wrapper);
    assert.equal(options.length, fakeGroupSets.length);
    assert.notCalled(onChangeGroupConfig);

    options.forEach((option, i) => {
      onChangeGroupConfig.resetHistory();

      select.props().onChange(option.prop('value'));

      assert.calledWith(onChangeGroupConfig, {
        useGroupSet: true,
        groupSet: fakeGroupSets[i].id,
      });
    });
  });

  it('prompts for authorization if needed', async () => {
    fakeIsAuthorizationError.returns(true);
    fakeAPICall
      .withArgs(groupSetsAPIRequest)
      .rejects(new Error('Authorization failed'));
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
    });

    // Check that authorization modal is shown if initial group set fetch fails.
    const authModal = await waitForElement(wrapper, 'AuthorizationModal');
    assert.equal(authModal.prop('authURL'), authURL);
    assert.equal(authModal.prop('authToken'), 'valid-token');

    // Check that group sets are fetched and rendered after authorization completes.
    fakeAPICall.withArgs(groupSetsAPIRequest).resolves(fakeGroupSets);
    authModal.prop('onAuthComplete')();
    wrapper.update();

    const { options } = await getOpenSelect(wrapper);
    assert.equal(options.length, fakeGroupSets.length);
  });

  it('shows a specific error message if the retrieved group set list is empty', async () => {
    fakeAPICall.withArgs(groupSetsAPIRequest).resolves([]);

    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
    });

    const errorModal = await waitForElement(wrapper, 'NoGroupsError');
    assert.include(
      errorModal.text(),
      'we could not find any available group sets in this course',
    );
  });

  it('shows errors in a modal with a retry button', async () => {
    fakeIsAuthorizationError.returns(false);
    fakeAPICall.withArgs(groupSetsAPIRequest).rejects(new Error('Some error'));
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
    });

    const authModal = await waitForElement(wrapper, 'ErrorModal');

    fakeAPICall.withArgs(groupSetsAPIRequest).resolves(fakeGroupSets);
    act(() => {
      authModal.prop('onRetry')();
    });
    wrapper.update();

    const { options } = await getOpenSelect(wrapper);
    assert.equal(options.length, fakeGroupSets.length);
  });

  it('unchecks checkbox if user cancels out of error modal', async () => {
    fakeIsAuthorizationError.returns(false);
    fakeAPICall.withArgs(groupSetsAPIRequest).rejects(new Error('Some error'));
    const onChangeGroupConfig = sinon.stub();

    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
      onChangeGroupConfig,
    });

    const authModal = await waitForElement(wrapper, 'ErrorModal');

    act(() => {
      authModal.prop('onCancel')();
    });

    // onChangeGroupConfig should be called with `useGroupSet: false`. This has
    // the side effect of un-checking the checkbox.
    assert.calledOnce(onChangeGroupConfig);
    assert.calledWith(onChangeGroupConfig, {
      useGroupSet: false,
      groupSet: null,
    });
  });
});
