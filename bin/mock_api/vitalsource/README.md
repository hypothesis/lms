# VitalSource Mock API

This is a https://mockoon.com/ format Mock API. You can [install this tool as
described here](https://mockoon.com/download/).

To use this mock for testing LMS you will need to:

 * Change the `lms.service.vitalsource._client.Client` attribute `VS_API` to:
    `http://localhost:3001`
 * Change your Vitalsource API key to `API_KEY`