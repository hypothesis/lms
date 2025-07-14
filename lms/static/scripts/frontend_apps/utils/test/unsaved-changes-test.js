import sinon from 'sinon';

import {
  hasUnsavedChanges,
  incrementUnsavedCount,
  decrementUnsavedCount,
} from '../unsaved-changes';

describe('unsaved-changes', () => {
  let addEventListenerStub;
  let removeEventListenerStub;

  beforeEach(() => {
    addEventListenerStub = sinon.stub(window, 'addEventListener');
    removeEventListenerStub = sinon.stub(window, 'removeEventListener');
  });

  afterEach(() => {
    while (hasUnsavedChanges()) {
      decrementUnsavedCount();
    }
    sinon.restore();
  });

  describe('hasUnsavedChanges', () => {
    it('returns false initially', () => {
      assert.isFalse(hasUnsavedChanges());
    });

    it('returns true after incrementing count', () => {
      incrementUnsavedCount();
      assert.isTrue(hasUnsavedChanges());
    });

    it('returns false after decrementing count to zero', () => {
      incrementUnsavedCount();
      decrementUnsavedCount();
      assert.isFalse(hasUnsavedChanges());
    });
  });

  describe('incrementUnsavedCount', () => {
    it('adds beforeunload listener when count goes from 0 to 1', () => {
      incrementUnsavedCount();
      assert.calledOnce(addEventListenerStub);
      assert.calledWith(addEventListenerStub, 'beforeunload');
    });

    it('does not add additional listeners when count is already > 0', () => {
      incrementUnsavedCount();
      incrementUnsavedCount();
      assert.calledOnce(addEventListenerStub);
    });
  });

  describe('decrementUnsavedCount', () => {
    it('removes beforeunload listener when count goes to 0', () => {
      incrementUnsavedCount();
      decrementUnsavedCount();
      assert.calledOnce(removeEventListenerStub);
      assert.calledWith(removeEventListenerStub, 'beforeunload');
    });

    it('does not remove listener when count is still > 0', () => {
      incrementUnsavedCount();
      incrementUnsavedCount();
      decrementUnsavedCount();
      assert.notCalled(removeEventListenerStub);
      assert.isTrue(hasUnsavedChanges());
    });

    it('does nothing when count is already 0', () => {
      decrementUnsavedCount();
      assert.notCalled(removeEventListenerStub);
      assert.isFalse(hasUnsavedChanges());
    });

    it('maintains count correctly after multiple operations', () => {
      incrementUnsavedCount();
      incrementUnsavedCount();
      decrementUnsavedCount();
      assert.isTrue(hasUnsavedChanges());
      decrementUnsavedCount();
      assert.isFalse(hasUnsavedChanges());
    });
  });

  describe('beforeunload handler', () => {
    it('prevents default and sets returnValue on beforeunload event', () => {
      incrementUnsavedCount();
      const preventUnload = addEventListenerStub.args[0][1];
      const mockEvent = {
        preventDefault: sinon.spy(),
        returnValue: false,
      };

      preventUnload(mockEvent);

      assert.calledOnce(mockEvent.preventDefault);
      assert.isTrue(mockEvent.returnValue);
    });
  });
});
