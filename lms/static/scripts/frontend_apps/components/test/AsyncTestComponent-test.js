import { createElement } from 'preact';
import { shallow } from 'enzyme';

import AsyncTestComponent, { $imports } from '../AsyncTestComponent';

describe('AsyncTestComponent', () => {
  let fakeAsyncMethod;

  const renderForm = (props = {}) => {
    return shallow(<AsyncTestComponent {...props} />);
  };

  it('does not set the first value when the fakeAsyncMethod does not resolve', async () => {
    const wrapper = renderForm({ firstValue: 'first_' });
    assert.equal(wrapper.text(), 'initial_value');
  });

  context('Tries to set 1 value in a try block, after an async call', () => {
    beforeEach(() => {
      fakeAsyncMethod = sinon.stub();
      $imports.$mock({
        './AsyncTestComponentMethod': fakeAsyncMethod,
      });
    });
    afterEach(() => {
      $imports.$restore();
    });

    it('does not set the first value when the fakeAsyncMethod does not resolve', async () => {
      const wrapper = renderForm({ firstValue: 'first_' });
      assert.equal(wrapper.text(), 'initial_value');
    });

    it('does not set the first value when the fakeAsyncMethod resolves but it not awaited', async () => {
      fakeAsyncMethod.resolves('async_value');
      const wrapper = renderForm({ firstValue: 'first_' });
      assert.equal(wrapper.text(), 'initial_value');
    });

    it('sets the first value but does not append the value from the fakeAsyncMethod method', async () => {
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.resolves();
      assert.equal(wrapper.text(), 'first_undefined');
    });

    it('sets the first value and appends the async value', async () => {
      fakeAsyncMethod.resolves('async_value');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.resolves();
      assert.equal(wrapper.text(), 'first_async_value');
    });

    it('the value returned form the await does not matter, only the value from the first stub matters', async () => {
      fakeAsyncMethod.resolves('async_value');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.resolves('this value does not matter');
      assert.equal(wrapper.text(), 'first_async_value');
    });
  });

  context('when an exception happens', () => {
    beforeEach(() => {
      fakeAsyncMethod = sinon.stub();
      $imports.$mock({
        './AsyncTestComponentMethod': fakeAsyncMethod,
      });
    });
    afterEach(() => {
      $imports.$restore();
    });

    it('does not set the error if it resolves before it throws on the await', async () => {
      fakeAsyncMethod.resolves('async_value');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.throws('error');
      assert.equal(wrapper.text(), 'first_async_value');
    });

    it('same as prev test, but with rejects instead of throws', async () => {
      fakeAsyncMethod.resolves('async_value');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.rejects('async_error2');
      assert.equal(wrapper.text(), 'first_async_value');
    });

    it('throws an error, but does not update the state with an error message', async () => {
      fakeAsyncMethod.throws('async_error');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.resolves('async_value2');
      assert.equal(wrapper.text(), 'initial_value');
    });

    it('throws an error, but does not update the state with an error message even with a try block', async () => {
      fakeAsyncMethod.rejects('async_error');
      const wrapper = renderForm({ firstValue: 'first_' });
      try {
        await fakeAsyncMethod.rejects('async_error2');
      } catch (e) {
        //
      }
      assert.equal(wrapper.text(), 'initial_value');
    });

    it('rejects twice in a row, but does not set the error value', async () => {
      fakeAsyncMethod.rejects('async_error');
      const wrapper = renderForm({ firstValue: 'first_' });
      await fakeAsyncMethod.rejects('async_error2');
      await fakeAsyncMethod.rejects('async_error2');
      assert.equal(wrapper.text(), 'initial_value');
    });

    it('rejects twice in a row in an try block, and it sets the error value', async () => {
      fakeAsyncMethod.rejects('async_error');
      const wrapper = renderForm({ firstValue: 'first_' });
      try {
        await fakeAsyncMethod.rejects('async_error2');
        await fakeAsyncMethod.rejects('async_error2');
      } catch (e) {
        //
      }
      assert.equal(wrapper.text(), 'async_error');
    });
  });

  context(
    'Tries to set 2 values, both after an async call. One in a try block, the other after the try block',
    () => {
      beforeEach(() => {
        fakeAsyncMethod = sinon.stub();
        $imports.$mock({
          './AsyncTestComponentMethod': fakeAsyncMethod,
        });
      });
      afterEach(() => {
        $imports.$restore();
      });

      it('does not set the second value', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        await fakeAsyncMethod.resolves();
        assert.equal(wrapper.text(), 'first_async_value');
      });

      it('does not set the second value even with await and update', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        await fakeAsyncMethod.resolves();
        wrapper.update();
        assert.equal(wrapper.text(), 'first_async_value');
      });

      it('does not set the second value even with await and update and a try block', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        try {
          await fakeAsyncMethod.resolves();
          wrapper.update();
        } catch (e) {
          //
        }
        assert.equal(wrapper.text(), 'first_async_value');
      });

      it('does not set the second value even two awaited fakeAsyncMethod calls', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        await fakeAsyncMethod.resolves();
        await fakeAsyncMethod.resolves();
        assert.equal(wrapper.text(), 'first_async_value');
      });

      it('does not set the second value even two awaited fakeAsyncMethod calls and an update', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        await fakeAsyncMethod.resolves();
        await fakeAsyncMethod.resolves();
        wrapper.update();
        assert.equal(wrapper.text(), 'first_async_value');
      });

      it('sets the second value', async () => {
        fakeAsyncMethod.resolves('async_value');
        const wrapper = renderForm({
          firstValue: 'first_',
          secondValue: 'second_',
        });
        try {
          await fakeAsyncMethod.resolves();
          await fakeAsyncMethod.resolves();
        } catch (e) {
          //
        }
        assert.equal(wrapper.text(), 'second_');
      });
    }
  );
});
