import { createContext } from 'preact';

/**
 * Parameters for an API call that the frontend can make to the server.
 *
 * The parameters of the call are decided by the backend, but the frontend
 * decides _when_ to make the call and what to show while waiting for the
 * response.
 *
 * @typedef APICallInfo
 * @prop {string} path - The complete URL or path of the API call
 * @prop {string} [authUrl] -
 *   URL to display in a popup window if the call fails due to an authorization
 *   error. This is used when the API call requires an OAuth 2 authorization
 *   flow to be completed with eg. an external LMS's API
 * @prop {object} [data]
 */

/**
 * Configuration determining which "mode" the frontend app should operate in.
 * Each mode maps to an app-level UI component.
 *
 * @typedef {'basic-lti-launch'|'content-item-selection'|'error-dialog'|'oauth2-redirect-error'} AppMode
 *
 */

/**
 * @typedef StudentInfo
 * @prop {string} displayName
 * @prop {string} userid - Identifier for student user in `h`
 * @prop {string} LISResultSourcedId - Unique outcome identifier
 * @prop {string} LISOutcomeServiceUrl - API URL for posting outcome results
 * @prop {string} lmsId - LMS-generated identifier for student user
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
 * @prop {object} submissionParams
 */

/**
 * Configuration used to launch the VitalSource book viewer.
 *
 * See `VitalSourceService` in the backend for details of the configuration
 * parameters.
 *
 * @typedef VitalSourceConfig
 * @prop {string} launchUrl - URL for the `<form>` used to launch the viewer
 * @prop {Record<string,string>} launchParams - Form field names and values
 */

/**
 * Configuration for the content/file picker app shown while configuring an
 * assignment.
 *
 * @typedef FilePickerConfig
 * @prop {string} formAction
 * @prop {Record<string,string>} formFields
 * @prop {APICallInfo} createAssignmentAPI
 * @prop {string} ltiLaunchUrl
 * @prop {object} blackboard
 *   @prop {boolean} blackboard.enabled
 *   @prop {boolean} blackboard.groupsEnabled
 *   @prop {APICallInfo} blackboard.listFiles
 *   @prop {APICallInfo} blackboard.listGroupSets
 * @prop {object} canvas
 *   @prop {boolean} canvas.enabled
 *   @prop {boolean} canvas.groupsEnabled
 *   @prop {APICallInfo} canvas.listFiles
 *   @prop {APICallInfo} canvas.listGroupSets
 * @prop {object} google
 *   @prop {string} google.clientId
 *   @prop {string} google.developerKey
 *   @prop {string} google.origin
 * @prop {object} microsoftOneDrive
 *   @prop {boolean} microsoftOneDrive.enabled
 *   @prop {string} [microsoftOneDrive.clientId]
 *   @prop {string} [microsoftOneDrive.redirectURI]
 * @prop {Object} vitalSource
 *   @prop {boolean} vitalSource.enabled
 */

/**
 * @typedef {import('./errors').AppLaunchServerErrorCode} AppLaunchServerErrorCode
 * @typedef {import('./errors').OAuthServerErrorCode} OAuthServerErrorCode
 */
/**
 * Base type for error information provided through this configuration object.
 *
 * @typedef ConfigErrorBase
 * @prop {AppLaunchServerErrorCode|OAuthServerErrorCode} [errorCode]
 * @prop {object|string} [errorDetails]
 */

/**
 * Configuration for information describing general errors for use in
 * `error-dialog` mode.
 *
 * @typedef ErrorDialogConfigBase
 * @prop {AppLaunchServerErrorCode} [errorCode]
 *
 * @typedef {ConfigErrorBase & ErrorDialogConfigBase} ErrorDialogConfig
 */

/**
 * Configuration for information describing errors specific to
 * OAuth API fails for use in `oauth2-redirect-error` mode. This adds a couple
 * of additional optional properties to the base ConfigErrorCode type.
 *
 * @typedef OAuthErrorConfigBase
 * @prop {OAuthServerErrorCode} [errorCode]
 * @prop {string} [authUrl]
 * @prop {string[]} [canvasScopes]
 *
 * @typedef {ConfigErrorBase & OAuthErrorConfigBase} OAuthErrorConfig
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
 * @prop {AppMode} mode
 * @prop {object} api
 *   @prop {string} api.authToken
 *   @prop {APICallInfo} api.sync
 *   @prop {APICallInfo} api.viaUrl
 * @prop {object} canvas
 *   @prop {SpeedGraderConfig} canvas.speedGrader
 * @prop {boolean} dev
 * @prop {FilePickerConfig} filePicker
 * @prop {GradingConfig} grading
 * @prop {object} hypothesisClient
 * @prop {object} rpcServer
 *   @prop {string[]} rpcServer.allowedOrigins
 * @prop {string} viaUrl
 * @prop {OAuthErrorConfig} OAuth2RedirectError
 * @prop {ErrorDialogConfig} errorDialog
 * @prop {VitalSourceConfig} [vitalSource]
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

  try {
    const config = JSON.parse(/** @type {string} */ (configEl.textContent));
    return config;
  } catch (err) {
    throw new Error('Failed to parse frontend configuration');
  }
}
