# Changelog

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
- Method in the the new Python SDK Client for downloading the custom userstore sdk for your userstore (DownloadUserstoreSDK).
- Userstore SDK now includes methods like UpdateUserForPurposes which allows you to pass the purposes in as an array of enum constants.
