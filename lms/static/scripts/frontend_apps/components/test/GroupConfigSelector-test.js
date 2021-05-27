import { mount } from 'enzyme';
import { createElement } from 'preact';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { waitForElement } from '../../../test-util/wait';
import { Config } from '../../config';
import GroupConfigSelector, { $imports } from '../GroupConfigSelector';

describe('GroupConfigSelector', () => {
  const authURL = 'https://testlms.hypothes.is/authorize';
  const groupSetsAPIRequest = {
    authToken: 'valid-token',
    path: '/api/group-sets',
  };

  let fakeAPICall;
  let fakeConfig;
  let fakeGroupSets;

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

    fakeAPICall = sinon.stub();
    fakeAPICall.withArgs(groupSetsAPIRequest).resolves(fakeGroupSets);
    fakeConfig = {
      api: { authToken: groupSetsAPIRequest.authToken },
      filePicker: {
        canvas: {
          listGroupSets: {
            authUrl: authURL,
            path: groupSetsAPIRequest.path,
          },
        },
      },
    };

    $imports.$mock(mockImportedComponents());

    // Avoid mocking shared components so we can treat them just like native
    // form controls. We might want to do this for other tests in future.
    $imports.$restore({
      '@hypothesis/frontend-shared': true,
    });

    $imports.$mock({
      '../utils/api': { apiCall: fakeAPICall },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent(props = {}) {
    const noop = () => {};
    return mount(
      <Config.Provider value={fakeConfig}>
        <GroupConfigSelector
          groupConfig={{ useGroupSet: false, groupSet: null }}
          onChangeGroupConfig={noop}
          {...props}
        />
      </Config.Provider>
    );
  }

  function toggleCheckbox(wrapper) {
    const checkbox = wrapper.find('input[type="checkbox"]');
    checkbox.getDOMNode().click();
    checkbox.simulate('input');
  }

  [
    [{ useGroupSet: false, groupSet: null }, false],
    [{ useGroupSet: true, groupSet: null }, true],
  ].forEach(([groupConfig, shouldBeChecked], index) => {
    it(`sets checkbox state to reflect \`useGroupSet\` state (${index})`, () => {
      const wrapper = createComponent({ groupConfig });
      assert.equal(
        wrapper.find('LabeledCheckbox').prop('checked'),
        shouldBeChecked
      );
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

    // While groups are being fetched, the `<select>` should be visible but disabled
    // and display a fetching status.
    const groupSetSelect = wrapper.find('select');
    assert.isTrue(groupSetSelect.exists());
    assert.isTrue(groupSetSelect.prop('disabled'));
    assert.equal(groupSetSelect.find('option').length, 1);
    assert.equal(groupSetSelect.find('option').text(), 'Fetching group sets…');

    // Once group sets are fetched, they should be rendered as `<option>`s.
    const options = await waitForElement(
      wrapper,
      'option[data-testid="groupset-option"]'
    );
    assert.equal(options.length, fakeGroupSets.length);

    fakeGroupSets.forEach((gs, i) => {
      assert.equal(options.at(i).text(), gs.name);
      assert.equal(options.at(i).prop('value'), gs.id);
    });
  });

  it('invokes `onChangeGroupConfig` callback when a group set is selected', async () => {
    const onChangeGroupConfig = sinon.stub();
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
      onChangeGroupConfig,
    });

    const options = await waitForElement(
      wrapper,
      'option[data-testid="groupset-option"]'
    );
    assert.equal(options.length, fakeGroupSets.length);
    assert.notCalled(onChangeGroupConfig);

    const select = wrapper.find('select').getDOMNode();

    options.forEach((option, i) => {
      onChangeGroupConfig.resetHistory();

      select.value = option.prop('value');
      select.dispatchEvent(new Event('input'));

      assert.calledWith(onChangeGroupConfig, {
        useGroupSet: true,
        groupSet: fakeGroupSets[i].id,
      });
    });
  });

  it('prompts for authorization if needed', async () => {
    fakeAPICall
      .withArgs(groupSetsAPIRequest)
      .rejects(new Error('Authorization failed'));
    const wrapper = createComponent({
      groupConfig: { useGroupSet: true, groupSet: null },
    });

    // Check that authorization prompt is shown if initial group set fetch fails.
    const authButton = await waitForElement(wrapper, 'AuthButton');
    assert.equal(authButton.prop('authURL'), authURL);
    assert.equal(authButton.prop('authToken'), 'valid-token');

    // Check that group sets are fetched and rendered after authorization completes.
    fakeAPICall.withArgs(groupSetsAPIRequest).resolves(fakeGroupSets);
    authButton.prop('onAuthComplete')();

    const options = await waitForElement(
      wrapper,
      'option[data-testid="groupset-option"]'
    );
    assert.equal(options.length, fakeGroupSets.length);
  });
});
