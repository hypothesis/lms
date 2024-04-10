import { render } from 'preact';

import type { DashboardConfig } from '../config';

/**
 * Handles the rendering and submitting of the form which is used to open the
 * instructor dashboard
 */
export class DashboardOpeningFormController {
  private _dashboardConfig: DashboardConfig;
  private _authToken: string;

  constructor(dashboardConfig: DashboardConfig, authToken: string) {
    this._dashboardConfig = dashboardConfig;
    this._authToken = authToken;
  }

  render() {
    const container = document.createElement('div');
    document.body.append(container);

    const destroy = () => {
      render(null, container);
      container.remove();
    };

    render(
      <form
        target="_blank"
        method="POST"
        action={this._dashboardConfig.dashboardEntryPoint.path}
        ref={form => {
          if (!form) {
            return;
          }

          // Immediately submit the form, as soon as it has been mounted
          form.submit();
          destroy();
        }}
        data-testid="dashboard-opening-form"
      >
        <input type="hidden" name="authorization" value={this._authToken} />
      </form>,
      container,
    );
  }
}
