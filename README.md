# Project status
![status: inactive](https://img.shields.io/badge/status-inactive-red.svg)

This project is no longer actively maintained, and remains here as an archive of this work.

instantbuy-sample-python
=======================

Basic python implementation of the Google Wallet for Instant Buy API.

### Setup

To setup the sample app.

*  If you don't already have a Google contact, submit the [Instant buy interest form](http://getinstantbuy.withgoogle.com). Google will respond to qualified merchants with instructions on how to set up merchant credentials.
* Replace MERCHANT_ID, MERCHANT_SECRET, MERCHANT_NAME in main.py with your Merchant Id, Merchant Secret Key, Merchant Name.
* Create an API project in the [Google API Console](https://code.google.com/apis/console/) then select the API Access tab in your API project, and click Create an OAuth 2.0 client ID and also enable Google+ API in services tab.
* Replace CLIENT_ID, ORIGIN with your OAUTH Client Id and Application Origin Url.

### Google appengine.

Setup your application on Google appengine.

1. Create new application at your appengine account.
2. Change application name in app.yaml file.
3. Follow instruction to install google appengine sdk for python and to upload the application on Google Appengine for Python Docs
4. Upload your application on google appengine.
5. Run your application from google appengine.
