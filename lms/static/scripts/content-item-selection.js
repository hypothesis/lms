// The "gapi" and "google" globals come from https://apis.google.com/js/api.js
// which must be loaded before any functions referencing those globals are invoked.

/* global gapi, google */

// TODO: handle form validation!
const state = {
  selectedDocId: null,
  selectedDocUrl: null,
};

function addHttp(url) {
  if (url !== '' && !/^(f|ht)tps?:\/\//i.test(url)) {
    url = 'http://' + url;
  }
  return url;
}

function addHttps(url) {
  if (url !== '' && !/^(f|ht)tps?:\/\//i.test(url)) {
    url = 'https://' + url;
  }
  return url;
}

function resetError(input) {
  input.parentElement.classList.remove('has-error');
  input.parentElement.getElementsByClassName('error')[0].innerHTML = '';
}

function handleSubmit(event, form) {
  if (form.elements.document_url.value.length === 0) {
    event.preventDefault();
    form.getElementsByClassName('input')[0].classList.add('has-error');
    form.getElementsByClassName('error')[0].innerHTML = 'Please enter a valid url';
  }
  let docInfo;
  if (form.elements.document_url.value.indexOf('?') !== 0) {
    docInfo = '?url=' +addHttp(form.elements.document_url.value);
  } else {
    docInfo = form.elements.document_url.value;
  }
  const launchUrl = window.DEFAULT_SETTINGS.ltiLaunchUrl + docInfo;
  const contentItem = {
    '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
    '@graph': [
      {
        '@type': 'LtiLinkItem',
        mediaType: 'application/vnd.ims.lti.v1.ltilink',
        url: launchUrl,
      },
    ],
  };

  form.elements.content_items.value = JSON.stringify(contentItem);

  // If the user submits the google picker selected url, then we should
  // make that file public. If they use the picker and then change the url,
  // we should not make the selected file public.
  const urlSelectedDocUrl = '?url=' + state.selectedDocUrl;
  if (state.selectedDocId && state.selectedDocUrl && docInfo === urlSelectedDocUrl) {
    // If we need to make a file public, then we need to stop the event so we
    // can wait until the 'enable public viewing' request resolves before
    // resubmitting the form. Otherwise the content item selection window
    // will close and the request will be terminated.

    event.preventDefault();
    enablePublicViewing(
      state.selectedDocId,
      () => {
        state.selectedDocId = null;
        state.selectedDocUrl = null;
        form.submit();
      }, (err) => {
        state.selectedDocId = null;
        state.selectedDocUrl = null;
        form.submit();
        throw new Error(err);
      }
    );
  }
}

////////  Google Picker Integration ///////

/////// Google Picker /////////
// The Browser API key obtained from the Google API Console.
const developerKey = window.DEFAULT_SETTINGS.googleDeveloperKey;

// The Client ID obtained from the Google API Console. Replace with your own Client ID.
const clientId = window.DEFAULT_SETTINGS.googleClientId;

// Scope to use to access user's Drive items.
const scopes = ['https://www.googleapis.com/auth/drive'];

// Array of API discovery doc URLs for APIs used by the quickstart
const DISCOVERY_DOCS = ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'];

const GOOGLE_MIME_TYPES = {
  // 'application/vnd.google-apps.document': 'googleDocs', // Note: we can
  // reenable google documents when we figure out how to make hypothesis
  // support pdf exports
  'application/pdf': 'googleDriveFile',
};

/** The `gapi.auth2.GoogleAuth` instance returned by `gapi.auth2.init`. */
let googleAuth = null;

/**
 * Promise which resolves when the Google API client libraries are loaded.
 *
 * Loading is triggered by a callback to the `gapiLoaded` function when the
 * apis.google.com/js/api.js script finishes loading.
 */
const googleApisLoaded = new Promise((resolve, reject) => {
  window.gapiLoaded = () => {
    gapi.load('client:auth2:picker', {
      callback: resolve,
      onerror: reject,
    });
  };
}).then(() => {
  // Initialize the `gapi.auth2` library. This must happen before attempting
  // to sign in.
  return gapi.auth2.init({
    client_id: clientId,
    scope: scopes.join(' '),
  });
}).then((googleAuth_) => {
  googleAuth = googleAuth_;
}).catch(onLoadError);

/**
 * Handle Google picker button click.
 *
 * Initialize the Google API client, authorize the user and then show the
 * Google file picker.
 */
function showGoogleDriveFilePicker(event) {
  event.preventDefault();

  googleApisLoaded.then(() => {
    return Promise.all([authorizeGoogleDriveAccess(), initGoogleClient()]);
  }).then(([accessToken]) => {
    const mimeTypes = Object.keys(GOOGLE_MIME_TYPES).join(',');
    const view = new google.picker.View(google.picker.ViewId.DOCS);
    view.setMimeTypes(mimeTypes);
    const picker = new google.picker.PickerBuilder()
      .setOrigin(addHttps(window.DEFAULT_SETTINGS.lmsUrl))
      .setOAuthToken(accessToken)
      .addView(view)
      .addView(new google.picker.DocsUploadView())
      .setDeveloperKey(developerKey)
      .setCallback(pickerCallback)
      .build();
    picker.setVisible(true);
  });
}

function onLoadError(e) {
  throw new Error('Error loading Google Api: ' + e.message);
}

/** Initialize the `gapi.client` library. */
function initGoogleClient() {
  return gapi.client.init({
    apiKey: developerKey,
    clientId: clientId,
    discoveryDocs: DISCOVERY_DOCS,
    scope: scopes.join(' '),
  });
}

function enablePublicViewing(docId, onSuccess, onFailure) {
  const body = {
    'type': 'anyone',
    'role': 'reader',
  };
  const request = gapi.client.drive.permissions.create({
    'fileId': docId,
    'resource': body,
  });
  request.execute(onSuccess, onFailure);
}

/**
 * Request access to the user's data in Google Drive.
 */
function authorizeGoogleDriveAccess() {
  return googleAuth.signIn().then((user) => {
    return user.getAuthResponse();
  }).then((authResponse) => {
    return authResponse.access_token;
  });
}

////////// Google Url Support /////////////////
function buildDocUrl(doc) {
  const urlBuilder = GOOGLE_MIME_TYPES[doc.mimeType];
  switch (urlBuilder) {
  case 'googleDocs':
    return googleDocUrl(doc);
  case 'googleDriveFile':
    return googleDriveFileUrl(doc);
  default:
    throw new Error('Mime type not supported');
  }
}

function googleDriveFileUrl(doc) {
  return 'https://drive.google.com/uc?id='
    + doc.id
    + '&authuser=0&export=download';
}

function googleDocUrl(doc) {
  return 'https://docs.google.com/document/d/'
    + doc.id
    + '/export?format=pdf';
}

function pickerCallback(data) {
  const docCount = data.docs && data.docs.length;
  if (data.action === google.picker.Action.PICKED && docCount === 1) {
    const doc = data.docs[0];
    const url = buildDocUrl(doc);
    state.selectedDocId = doc.id;
    state.selectedDocUrl = url;
    if (url) {
      const input = document.getElementById('launch-form').elements.document_url;
      input.value = url;
      resetError(input);
    } else {
      throw new Error('Document url could not be constructed');
    }
  }
}

// Expose public API for use by server-rendered form in the content_item_selection
// template.
window.contentItemSelection = {
  handleSubmit,
  showGoogleDriveFilePicker,
  resetError,
};
