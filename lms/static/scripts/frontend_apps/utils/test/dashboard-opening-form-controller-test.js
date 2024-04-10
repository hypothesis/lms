import { DashboardOpeningFormController } from '../dashboard-opening-form-controller';

describe('DashboardOpeningFormController', () => {
  let controller;

  beforeEach(() => {
    sinon.stub(window.HTMLFormElement.prototype, 'submit');

    controller = new DashboardOpeningFormController(
      {
        dashboardEntryPoint: { path: '/dashboard' },
      },
      'token',
    );
  });

  afterEach(() => {
    window.HTMLFormElement.prototype.submit.restore();
  });

  describe('render', () => {
    it('submits form and removes it from DOM', () => {
      assert.notCalled(window.HTMLFormElement.prototype.submit);
      controller.render();

      assert.called(window.HTMLFormElement.prototype.submit);
      assert.isNull(
        document.querySelector('[data-testid="dashboard-opening-form"]'),
      );
    });
  });
});
