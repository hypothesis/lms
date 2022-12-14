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
 * Configuration for the content/file picker app shown while configuring an
 * assignment.
 *
 * @typedef FilePickerConfig
 * @prop {string} formAction
 * @prop {Record<string,string>} formFields
 * @prop {APICallInfo} [deepLinkingAPI]
 * @prop {string} ltiLaunchUrl
 * @prop {object} blackboard
 *   @prop {boolean} blackboard.enabled
 *   @prop {APICallInfo} blackboard.listFiles
 * @prop {object} d2l
 *   @prop {boolean} d2l.enabled
 *   @prop {APICallInfo} d2l.listFiles
 * @prop {object} canvas
 *   @prop {boolean} canvas.enabled
 *   @prop {APICallInfo} canvas.listFiles
 * @prop {object} google
 *   @prop {string} google.clientId
 *   @prop {string} google.developerKey
 *   @prop {string} google.origin
 * @prop {object} jstor
 *   @prop {boolean} jstor.enabled
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
 * @prop {string} [errorMessage]
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
 * @typedef ServiceConfig
 * @prop {string} grantToken
 */

/**
 * The subset of the Hypothesis client configuration that this app directly references.
 *
 * The backend will add other properties which are intentionally not included here,
 * even as an index signature. This other configuration is simply forwarded to
 * the client.
 *
 * See https://h.readthedocs.io/projects/client/en/latest/publishers/config/.
 *
 * @typedef ClientConfig
 * @prop {[ServiceConfig]} services - Annotation configuration for the client.
 *   In the LMS context this will always consist of exactly one entry.
 * @prop {object} [reportActivity] - When present, enables communication of
 *   annotation activity from the client sidebar's frame to this one.
 *   The details of this object can be considered opaque to this application,
 *   but its presence indicates that Canvas empty grading submissions should
 *   only be submitted for a student after qualifying annotation activity
 *   occurs (not immediately at launch).
 */

/**
 * Configuration for the content info banner which is displayed by the client.
 *
 * This banner is a contractual requirement for some document sources. It shows
 * basic document metadata along with relevant links into the content provider's
 * site.
 *
 * @typedef ContentBannerConfig
 * @prop {'jstor'} source - Identifier for the metadata source
 * @prop {string} itemId
 */

/**
 * Debug information sent by the backend.
 *
 * @typedef DebugInfo
 * @prop {string[]} [tags]
 * @prop {Record<string,any>} [values]
 */

/**
 * Settings of the current product
 *
 * @typedef ProductSettings
 * @prop {boolean} groupsEnabled
 */

/**
 * API endpoints for the product
 *
 * @typedef ProductAPI
 * @prop {APICallInfo} listGroupSets
 */

/**
 * Information about the current product
 *
 * @typedef Product
 * @prop {string} family
 * @prop {ProductSettings} settings
 * @prop {ProductAPI} api
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
 * @prop {ContentBannerConfig} [contentBanner]
 * @prop {boolean} dev
 * @prop {FilePickerConfig} filePicker
 * @prop {GradingConfig} grading
 * @prop {ClientConfig} hypothesisClient
 * @prop {object} rpcServer
 *   @prop {string[]} rpcServer.allowedOrigins
 * @prop {string} viaUrl
 * @prop {OAuthErrorConfig} OAuth2RedirectError
 * @prop {ErrorDialogConfig} errorDialog
 * @prop {DebugInfo} [debug]
 * @prop {Product} product
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
