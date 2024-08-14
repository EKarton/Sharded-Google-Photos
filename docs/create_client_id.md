# Creating your OAuth2 Google Client ID

## Description

This document outlines how to create your own OAuth2 client ID and client secrets so that you can interact with the Google Photos and Google Drive APIs.

## Steps

1. Go to <https://cloud.google.com/cloud-console> and log into your Google account
2. Click on the "Console" button:

<div width="100%">
    <p align="center">
<img src="image-1.png" width="600px"/>
    </p>
</div>

3. Click on the "Select Project" button and create a new project with any name:

<div width="100%">
    <p align="center">
<img src="image-2.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-3.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-4.png" width="600px"/>
    </p>
</div>

4. Wait for your project to be created. Then select your project again:

<div width="100%">
    <p align="center">
<img src="image-5.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-6.png" width="600px"/>
    </p>
</div>

5. Type in "Photos Library Api" in the search box, select "Photos Library Api", and click on "Enable":

<div width="100%">
    <p align="center">
<img src="image-7.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-8.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-9.png" width="600px"/>
    </p>
</div>

6. Similarly, enable the Drive API by typing in "Drive API" in the search box, select "Drive API", and click on "Enable":

<div width="100%">
    <p align="center">
<img src="image-10.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-11.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-12.png" width="600px"/>
    </p>
</div>

7. Create a new OAuth2 Consent Screen by going to to the APIs and Services tab, creating an External API, and fill in the details:

<div width="100%">
    <p align="center">
<img src="image-13.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-14.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-15.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-16.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-17.png" width="600px"/>
    </p>
</div>

8. No special scopes is needed. So we can click on the `Save and Continue` button:

<div width="100%">
    <p align="center">
<img src="image-18.png" width="600px"/>
    </p>
</div>

9. In the Test Users page, click on `Save and Continue`. We don't need to add test users since we will publish the app:

<div width="100%">
    <p align="center">
<img src="image-19.png" width="600px"/>
    </p>
</div>

10. In the "Summary" page, scroll down and click on `Back to Dashboard` button:

<div width="100%">
    <p align="center">
<img src="image-20.png" width="600px"/>
    </p>
</div>

11. In the main consent page, click on `Publish App`. A dialog will appear. Click on `Confirm`. It will publish the app:

<div width="100%">
    <p align="center">
<img src="image-21.png" width="600px"/>
    </p>
</div>

12. Create the Client IDs and client secrets by going to the "Credentials" tab, clicking on "Create Credentials", select "OAuth Client ID", selecting "Web Application", and adding `http://localhost:8080/` in the authorized redirect uri:

<div width="100%">
    <p align="center">
<img src="image-22.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-23.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-24.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-25.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-26.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-27.png" width="600px"/>
    </p>
</div>

13. Finally, click on the `Create` button. A dialog will appear with your Client ID and Client secrets. Download the file named as `client_secrets.json` and you now have your own client ID and client secrets:

<div width="100%">
    <p align="center">
<img src="image-28.png" width="600px"/>
    </p>
</div>

<div width="100%">
    <p align="center">
<img src="image-29.png" width="600px"/>
    </p>
</div>
