Installing your local app in Canvas
===================================

### Enabling the Canvas File Picker

In order to use the Canvas file picker, you need to generate a developer key and ID within the target Canvas instance.

1. Log in to Canvas as an admin user
1. Navigate to `Admin` then click the name of the root account
1. Navigate to `Developer Keys`, then click `+ Developer Key`.
1. Fill out the form:
    1. For name and email you can enter whatever you please; leave the legacy redirect URI field blank
    1. For the `Redirect URIs` field enter:
        ```
        http://localhost:8001/canvas_oauth_callback
        ```

        *Note*: For QA, replace `localhost:8001` with `qa-lms.hypothes.is`; for production, replace it with `lms.hypothes.is`

     7. Click `Save Key`
 8. Take note of the resulting credentials:

    * The `ID` is the `Developer Key` needed in the following steps
    * The `key` is the `Developer Secret` needed in the following steps

### Installing the App for a Canvas (LMS) Course

#### Generating a consumer key and secret

The [http://localhost:8001/welcome](http://localhost:8001/welcome) tool is used to generate a consumer key and a secret that will be used when installing the Hypothesis LMS app for a Canvas (LMS) course.

1. With your [dev web server running](#run-webserver), visit [http://localhost:8001/welcome](http://localhost:8001/welcome) in a browser.
1. Enter the domain for the Canvas instance where the Hypothesis LMS app will be installed (e.g. `foo.instructure.com`)
1. Enter your email (any email is fine here)
1. To enable Canvas picker integration, enter the Developer Key and Developer Secret generated during the [the Canvas Picker configuration step](#canvas-picker) into the corresponding fields here

#### Installing the Hypothesis LMS app for a Canvas (LMS) Course

1. Log into the your Canvas instance as an admin user
1. Navigate to the course you'd like to add the Hypothesis app to
1. Add a new app for the course

    Navigate to `Settings` and then to the `Apps` tab. Click the `View App Configurations` button, and then the `+ App` (add an app) button.

1. Fill out the Add-App form

    * For `Configuration Type`, select `Paste XML`
    * Give your App a name
    * Enter the consumer key and secret you generated (above) in the provided fields
    * Visit [http://localhost:8001/config_xml](http://localhost:8001/config_xml) and paste the contents of the output into the `XML Configuration` field
    * Submitting the form should install the app and it should be available from within the Modules and Assignments areas of the course

### Configuring Assignments and Modules

**TODO**

When creating a new module or assignment, select `External Tool` and `Hypothesis` from the available list. This should allow you to choose a file from [Google Drive](#google-apis) or [Canvas](#canvas-picker) itself (if you have configured either of those features).
