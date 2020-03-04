import AuthWindow from '../AuthWindow';

describe('AuthWindow', () => {
  let fakePopup;
  beforeEach(() => {
    fakePopup = {
      focus: sinon.stub(),
      close: sinon.stub(),
      closed: false,
    };
    sinon.stub(window, 'open').returns(fakePopup);
  });

  afterEach(() => {
    window.open.restore();
  });

  function createAuthWindow() {
    return new AuthWindow({
      authToken: 'auth-token',
      authUrl: 'https://lms.anno.co/authorize',
    });
  }

  describe('#authorize', () => {
    it('shows auth popup window', () => {
      const authWin = createAuthWindow();
      authWin.authorize();
      assert.calledWith(
        window.open,
        'https://lms.anno.co/authorize?authorization=auth-token',
        'Allow access to Canvas files'
      );
    });

    it('rejects if the window cannot be opened', async () => {
      const authWin = createAuthWindow();
      window.open.returns(null);
      let reason;
      try {
        await authWin.authorize();
      } catch (err) {
        reason = err;
      }
      assert.instanceOf(reason, Error);
    });

    it('returns a Promise that resolves when the window is closed', async () => {
      const authWin = createAuthWindow();
      const authorized = authWin.authorize();

      fakePopup.closed = true;

      return await authorized;
    });
  });

  describe('#close', () => {
    it('does nothing if the popup is not open', () => {
      const authWin = createAuthWindow();
      authWin.close();
    });

    it('closes the popup window', async () => {
      const authWin = createAuthWindow();
      authWin.authorize();
      authWin.close();
      assert.called(fakePopup.close);
    });
  });

  describe('#focus', () => {
    it('focuses the popup window', async () => {
      const authWin = createAuthWindow();
      authWin.authorize();
      authWin.focus();
      assert.called(fakePopup.focus);
    });
  });
});
