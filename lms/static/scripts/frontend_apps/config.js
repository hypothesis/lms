import { createContext } from 'preact';

/**
 * Parameters for an "canned" API call that the frontend can make to the server.
 *
 * The parameters of the call are decided by the backend, but the frontend
 * decides _when_ to make the call and what to show while waiting for the
 * response.
 *
 * @typedef ApiCallInfo
 * @prop {string} path
 * @prop {Object} data
 */

/**
 * @typedef StudentInfo
 * @prop {string} displayName
 * @prop {string} userid
 */

/**
 * Data needed to render the grading bar shown when an instructor views an assignment.
 *
 * @typedef GradingConfig
 * @prop {string} assignmentName
 * @prop {string} courseName
 * @prop {boolean} enabled
 * @prop {StudentInfo[]} students
 */

/**
 * Data needed to record an assignment submission.
 *
 * @typedef SpeedGraderConfig
 * @prop {Object} submissionParams
 */

/**
 * Configuration for the content/file picker app shown while configuring an
 * assignment.
 *
 * @typedef FilePickerConfig
 * @prop {string} formAction
 * @prop {Object.<string,string>} formFields
 * @prop {Object} canvas
 *   @prop {boolean} canvas.enabled
 *   @prop {string} canvas.ltiLaunchUrl
 *   @prop {string} canvas.courseId
 * @prop {Object} google
 *   @prop {string} clientId
 *   @prop {string} developerKey
 *   @prop {string} origin
 */

/**
 * Configuration for the error dialog shown if authorizing access to the
 * Canvas API fails.
 *
 * @typedef CanvasAuthErrorConfig
 * @prop {string|null} authorizeUrl
 * @prop {boolean} invalidScope
 * @prop {string} errorDetails
 * @prop {string[]} scopes
 */

/**
 * Data/configuration needed for frontend applications in the LMS app.
 * The `mode` property specifies which frontend application should load and
 * the available configuration/data depends on the mode and LTI user role.
 *
 * The documentation for these properties lives in the `JSConfig` class in
 * the backend code.
 *
 * @typedef ConfigObject
 * @prop {string} mode
 * @prop {Object} api
 *   @prop {string} api.authToken
 *   @prop {ApiCallInfo} api.sync
 *   @prop {string} api.viaCallbackUrl
 * @prop {string} authUrl
 * @prop {Object} canvas
 *   @prop {string} canvas.authUrl
 *   @prop {SpeedGraderConfig} canvas.speedGrader
 * @prop {boolean} dev
 * @prop {FilePickerConfig} filePicker
 * @prop {GradingConfig} grading
 * @prop {Object} hypothesisClient
 * @prop {Object} rpcServer
 *   @prop {string[]} rpcServer.allowedOrigins
 * @prop {string} viaUrl
 * @prop {CanvasAuthErrorConfig} canvasOAuth2RedirectError
 */

/**
 * Configuration object for the file picker application, read from a JSON
 * script tag injected into the page by the backend.
 */

const defaultConfig = /** @type {any} */ ({ api: {} });

export const Config = createContext(
  /** @type {ConfigObject} */ (defaultConfig)
);

/**
 * Read frontend app configuration from a JSON `<script>` tag in the page
 * matching the selector ".js-config".
 *
 * @return {ConfigObject}
 */
export function readConfig() {
  const selector = '.js-config';
  const configEl = document.querySelector(selector);

  if (!configEl) {
    throw new Error(`No config object found for selector "${selector}"`);
  }

  const config = JSON.parse(/** @type {string} */ (configEl.textContent));
  return config;
}
