# Changelog

## 1.5.0 - UNPUBLISHED

- Add GetConsentedPurposesForUser method to the Python SDK Client.
- Add `__repr__` methods to some models to improve DX.

## 1.4.0 - 02-02-2024

- Breaking change: ColumnInputConfig now has data member "normalizer", previously referred to as "validator"
- Add "User-Agent" & "X-Usercloudssdk-Version" headers to all outgoing requests.
- Add an optional `session_name` kwarg to the `Client` constructor to allow extra information to be incremented into the User-Agent header.
- Add "region" parameter to CreateUser and CreateUserWithMutator to allow specifying in which region the user data should reside
- Rename "compositeunion" and "compositeintersection" types of access policies to "composite_or" and "composite_and"
- Breaking change: Added AsyncClient class and UCHttpAsyncClient interface to support asynchronous requests. As part of this, Error class was consolidated into UserCloudsSDKError, which may break any customers referencing it.
- Add support for column constraints, which enables custom composite columns as well as checks for immutability, uniqueness, and unique IDs within array columns
- Deprecate TENANT_URL, CLIENT_ID and CLIENT_SECRET in favor of USERCLOUDS_TENANT_URL, USERCLOUDS_CLIENT_ID and USERCLOUDS_CLIENT_SECRET environment variables. The deprecated environment variables will be removed in a future release (they still work in this release).

## 1.3.0 - 11-12-2023

- Introduce UCHttpClient to assist in custom HTTP clients by defining the interface in which UserClouds makes requests to [httpx](https://www.python-httpx.org/)
- Changing POST body format for authorization Create functions, and adding if_not_exists option to CreateOrganization. These are non-breaking changes, but older clients using the previous format will be deprecated eventually.

## 1.2.0 - 21-11-2023

- Cleanup httpx client usage.
  This is a breaking change to the HTTP client interface since we stopped passing the deprecated `data` argument to the httpx client methods (PUT & POST) and pass the `content` argument instead.
- Add more type annotations to models and add a couple of `__str__` methods to models.
- Add `include_example` argument to `DownloadUserstoreSDK` method.

## 1.1.1 - 08-11-2023

- Bring back passing kwargs to the HTTP client methods.

## 1.1.0 -- 08-11-2023

- Add CreateUserWithMutator method to Python SDK Client and example for how to use in userstore_sample.py

## 1.0.15 -- 30-10-2023

- Fix future compatibility (make sure the SDK doesn't break if server sends new fields).
- Fix handling HTTP 404 responses to some HTTP DELETE API calls.
- Add support for output_type and reuse_existing_token fields in transformers.
- Lazily request access token when needed instead of on client creation.
- Improve HTTP error handling in SDK

## 1.0.14 -- 12-10-2023

- Added a changelog
- Switched to using [httpx](https://www.python-httpx.org/) for HTTP requests instead of [requests](https://requests.readthedocs.io/en/master/).
- Allow overriding the default HTTP client with a custom one.
- Add SDK methods for managing retention durations for soft-deleted data.
- Various other cleanup to the code.
- Method in the new Python SDK Client for downloading the custom userstore sdk for your userstore (DownloadUserstoreSDK).
- Userstore SDK now includes methods like UpdateUserForPurposes which allows you to pass the purposes in as an array of enum constants.
