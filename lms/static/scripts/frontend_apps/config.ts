import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

import type { AppLaunchServerErrorCode, OAuthServerErrorCode } from './errors';

/**
 * Parameters for an API call that the frontend can make to the server.
 *
 * The parameters of the call are decided by the backend, but the frontend
 * decides _when_ to make the call and what to show while waiting for the
 * response.
 */
export type APICallInfo = {
  /** The complete URL or path of the API call */
  path: string;
  /**
   * URL to display in a popup window if the call fails due to an authorization
   * error. This is used when the API call requires an OAuth 2 authorization
   * flow to be completed with eg. an external LMS's API.
   */
  authUrl?: string | null;
  data?: object;
};

/**
 * Configuration determining which "mode" the frontend app should operate in.
 * Each mode maps to an app-level UI component.
 */
export type AppMode =
  | 'basic-lti-launch'
  | 'content-item-selection'
  | 'dashboard'
  | 'email-preferences'
  | 'error-dialog'
  | 'oauth2-redirect-error';

export type StudentInfo = {
  displayName: string;
  /** Identifier for student user in `h` */
  userid: string;
  /** Unique outcome identifier */
  LISResultSourcedId: string;
  /** API URL for posting outcome results */
  LISOutcomeServiceUrl: string;
  /** LMS-generated identifier for student user */
  lmsId: string;
};

/**
 * Data needed to render the grading bar shown when an instructor views an assignment.
 */
export type InstructorConfig = {
  assignmentName: string;
  courseName: string;
  editingEnabled: boolean;
  gradingEnabled: boolean;
  acceptGradingComments: boolean;
  students: StudentInfo[] | null;
  scoreMaximum: number | null;
};

/**
 * Data needed to record an assignment submission.
 */
export type SpeedGraderConfig = { submissionParams: object };

/**
 * Information about the current configuration of an assignment, for use when
 * re-configuring an assignment.
 */
export type AssignmentConfig = {
  group_set_id: string | null;
  document: {
    url: string;
  };
};

/**
 * Configuration for the content/file picker app shown while configuring an
 * assignment.
 */
export type FilePickerConfig = {
  formAction: string;
  formFields: Record<string, string>;
  promptForTitle: boolean;
  deepLinkingAPI?: APICallInfo;
  ltiLaunchUrl: string;
  blackboard: {
    enabled: boolean;
    listFiles: APICallInfo;
  };
  d2l: {
    enabled: boolean;
    listFiles: APICallInfo;
  };
  moodle: {
    enabled: boolean;
    listFiles: APICallInfo;
    pagesEnabled: boolean;
    listPages: APICallInfo;
  };
  canvas: {
    enabled: boolean;
    pagesEnabled?: boolean;
    foldersEnabled: boolean;
    listFiles: APICallInfo;
    listPages: APICallInfo;
  };
  canvasStudio: {
    enabled: boolean;
    listMedia: APICallInfo;
  };
  google: {
    enabled: boolean;
    clientId?: string;
    developerKey?: string;
    origin?: string;
  };
  jstor: {
    enabled: boolean;
  };
  youtube: {
    enabled: boolean;
  };
  microsoftOneDrive: {
    enabled: boolean;
    clientId?: string;
    redirectURI?: string;
  };
  vitalSource: {
    enabled: boolean;
  };
};

/**
 * Base type for error information provided through this configuration object.
 */
export type ConfigErrorBase = {
  errorCode?: AppLaunchServerErrorCode | OAuthServerErrorCode;
  errorDetails?: object | string;
  errorMessage?: string;
};

/**
 * Configuration for information describing general errors for use in
 * `error-dialog` mode.
 */
export type ErrorDialogConfig = ConfigErrorBase & {
  errorCode?: AppLaunchServerErrorCode;
};

/**
 * Configuration for information describing errors specific to
 * OAuth API fails for use in `oauth2-redirect-error` mode. This adds a couple
 * of additional optional properties to the base ConfigErrorCode type.
 */
export type OAuthErrorConfig = ConfigErrorBase & {
  errorCode?: OAuthServerErrorCode;
  authUrl?: string;
  canvasScopes?: string[];
};

export type ServiceConfig = { grantToken: string };

/**
 * The subset of the Hypothesis client configuration that this app directly references.
 *
 * The backend will add other properties which are intentionally not included here,
 * even as an index signature. This other configuration is simply forwarded to
 * the client.
 *
 * See https://h.readthedocs.io/projects/client/en/latest/publishers/config/.
 */
export type ClientConfig = {
  /**
   * Authentication configuration for the client. In the LMS context this will
   * always consist of exactly one entry.
   */
  services: [ServiceConfig];
  /**
   * When present, enables communication of annotation activity from the client
   * sidebar's frame to this one.  The details of this object can be considered
   * opaque to this application, but its presence indicates that Canvas empty
   * grading submissions should only be submitted for a student after qualifying
   * annotation activity occurs (not immediately at launch).
   */
  reportActivity?: object;
};

/**
 * Configuration for the content info banner which is displayed by the client.
 *
 * This banner is a contractual requirement for some document sources. It shows
 * basic document metadata along with relevant links into the content provider's
 * site.
 */
export type ContentBannerConfig = {
  /** Identifier for metadata source. */
  source: 'jstor';
  itemId: string;
};

/**
 * Debug information sent by the backend.
 */
export type DebugInfo = {
  tags?: string[];
  values?: Record<string, unknown>;
};

/**
 * Settings of the current product.
 */
export type ProductSettings = {
  groupsEnabled: boolean;
};

/**
 * API endpoints for the product.
 */
export type ProductAPI = {
  listGroupSets: APICallInfo;
};

/**
 * Information about the current product.
 */
export type Product = {
  family: string;
  settings: ProductSettings;
  api: ProductAPI;
};

export type WeekDay = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun';

export type SelectedDays = Record<WeekDay, boolean>;

export type EmailPreferences = {
  selectedDays: SelectedDays;
  flashMessage: string | null;
};

export type DashboardRoutes = {
  assignment: string;
  assignment_stats: string;
  course: string;
  course_assignment_stats: string;
};

export type DashboardConfig = {
  routes: DashboardRoutes;
};

/**
 * Data/configuration needed for frontend applications in the LMS app.
 * The `mode` property specifies which frontend application should load and
 * the available configuration/data depends on the mode and LTI user role.
 *
 * The documentation for these properties lives in the `JSConfig` class in
 * the backend code.
 */
export type ConfigObject = {
  // Configuration present in all modes.
  mode: AppMode;

  // Present in most modes.
  api?: {
    authToken: string;

    // Only present in "basic-lti-launch" mode.
    sync?: APICallInfo;
    viaUrl?: APICallInfo;
  };
  dev: boolean;
  debug?: DebugInfo;
  product: Product;

  // Only present in "basic-lti-launch" mode.
  canvas: {
    // Only present in Canvas.
    speedGrader?: SpeedGraderConfig;
  };
  contentBanner?: ContentBannerConfig;
  editing?: {
    getConfig: APICallInfo;
  };
  instructorToolbar?: InstructorConfig;
  hypothesisClient?: ClientConfig;
  rpcServer?: {
    allowedOrigins: string[];
  };
  viaUrl: string;

  // Only present in "error-dialog" mode.
  errorDialog?: ErrorDialogConfig;

  // Only present in "content-item-selection" mode.
  filePicker?: FilePickerConfig;

  // Only present if re-configuring an existing assignment.
  assignment?: AssignmentConfig;

  // Only present in "oauth2-redirect-error" mode.
  OAuth2RedirectError?: OAuthErrorConfig;

  // Only present in "email-preferences" mode.
  emailPreferences?: EmailPreferences;

  // Only present in "dashboard" mode
  dashboard?: DashboardConfig;
};

/**
 * Configuration object for the file picker application, read from a JSON
 * script tag injected into the page by the backend.
 */
const defaultConfig = { api: {} } as unknown;

export const Config = createContext(defaultConfig as ConfigObject);

/**
 * Utility that modifies a type by making properties matching `K` non-nullable.
 */
export type Ensure<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * Return the backend-provided configuration, requiring that the optional
 * fields specified by `requiredKeys` are set.
 *
 * nb. The `= never` makes the return type just `ConfigObject` if `requiredKeys`
 * is omitted, otherwise it would change all optional keys to required.
 */
export function useConfig<R extends keyof ConfigObject = never>(
  requiredKeys: R[] = [],
): Ensure<ConfigObject, R> {
  const config = useContext(Config);
  for (const key of requiredKeys) {
    if (!(key in config)) {
      throw new Error(`Required configuration key "${key}" not set`);
    }
  }
  return config as Ensure<ConfigObject, R>;
}

/**
 * Read frontend app configuration from a JSON `<script>` tag in the page
 * matching the selector ".js-config".
 */
export function readConfig(): ConfigObject {
  const selector = '.js-config';
  const configEl = document.querySelector(selector);

  if (!configEl) {
    throw new Error(`No config object found for selector "${selector}"`);
  }

  try {
    const config = JSON.parse(configEl.textContent!);
    return config;
  } catch (err) {
    throw new Error('Failed to parse frontend configuration');
  }
}
