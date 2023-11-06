from __future__ import annotations

import json
import os
import uuid
import warnings

from usercloudssdk.client import Client, Error
from usercloudssdk.constants import (
    COLUMN_INDEX_TYPE_INDEXED,
    COLUMN_INDEX_TYPE_NONE,
    DATA_TYPE_ADDRESS,
    DATA_TYPE_BOOLEAN,
    DATA_TYPE_STRING,
    POLICY_TYPE_COMPOSITE_INTERSECTION,
    TRANSFORM_TYPE_TOKENIZE_BY_VALUE,
    TRANSFORM_TYPE_TRANSFORM,
)
from usercloudssdk.models import (
    Accessor,
    AccessPolicy,
    AccessPolicyComponent,
    AccessPolicyTemplate,
    Column,
    ColumnInputConfig,
    ColumnOutputConfig,
    ColumnRetentionDuration,
    Mutator,
    Purpose,
    ResourceID,
    RetentionDuration,
    Transformer,
    UpdateColumnRetentionDurationRequest,
    UpdateColumnRetentionDurationsRequest,
    UserSelectorConfig,
)
from usercloudssdk.policies import (
    AccessPolicyOpen,
    TransformerPassThrough,
    ValidatorOpen,
)

client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"

# This sample shows you how to create new columns in the user store and create access
# policies governing access to the data inside those columns. It also shows you how to
# create, delete and execute accessors and mutators. To learn more about these
# concepts, see docs.userclouds.com.


_PHONE_NUMBER_COLUMN_NAME = "phone_number"
_PHONE_NUMBER_COLUMN_RESOURCE_ID = ResourceID(name=_PHONE_NUMBER_COLUMN_NAME)

_SECURITY_PURPOSE_NAME = "security"
_SECURITY_PURPOSE_RESOURCE_ID = ResourceID(name=_SECURITY_PURPOSE_NAME)

_EMAIL_COLUMN_NAME = "email"
_EMAIL_COLUMN_RESOURCE_ID = ResourceID(name=_EMAIL_COLUMN_NAME)


def setup(client: Client):
    # illustrate CRUD for columns
    col = client.CreateColumn(
        Column(
            id=None,
            name="temp_column",
            type=DATA_TYPE_BOOLEAN,
            is_array=False,
            default_value="",
            index_type=COLUMN_INDEX_TYPE_NONE,
        ),
        if_not_exists=True,
    )
    client.ListColumns()
    col = client.GetColumn(col.id)
    col.name = "temp_column_renamed"
    client.UpdateColumn(col)
    client.DeleteColumn(col.id)

    # create phone number, home address, and email columns
    phone_number = client.CreateColumn(
        Column(
            id=None,
            name=_PHONE_NUMBER_COLUMN_NAME,
            type=DATA_TYPE_STRING,
            is_array=False,
            default_value="",
            index_type=COLUMN_INDEX_TYPE_INDEXED,
        ),
        if_not_exists=True,
    )

    client.CreateColumn(
        Column(
            id=None,
            name="home_addresses",
            type=DATA_TYPE_ADDRESS,
            is_array=True,
            default_value="",
            index_type=COLUMN_INDEX_TYPE_NONE,
        ),
        if_not_exists=True,
    )

    client.CreateColumn(
        Column(
            id=None,
            name=_EMAIL_COLUMN_NAME,
            type=DATA_TYPE_STRING,
            is_array=False,
            default_value="",
            index_type=COLUMN_INDEX_TYPE_INDEXED,
        ),
        if_not_exists=True,
    )

    # illustrate CRUD for purposes
    purpose = client.CreatePurpose(
        Purpose(id=None, name="temp_purpose", description="temp_purpose_description"),
        if_not_exists=True,
    )
    client.ListPurposes()
    purpose = client.GetPurpose(purpose.id)
    purpose.description = "new description"
    client.UpdatePurpose(purpose)
    client.DeletePurpose(purpose.id)

    # create purposes for security, support and marketing
    security = client.CreatePurpose(
        Purpose(
            id=None,
            name=_SECURITY_PURPOSE_NAME,
            description="Allows access to the data in the columns for security purposes",
        ),
        if_not_exists=True,
    )

    support = client.CreatePurpose(
        Purpose(
            id=None,
            name="support",
            description="Allows access to the data in the columns for support purposes",
        ),
        if_not_exists=True,
    )

    client.CreatePurpose(
        Purpose(
            id=None,
            name="marketing",
            description="Allows access to the data in the columns for marketing purposes",
        ),
        if_not_exists=True,
    )

    # configure retention durations for soft-deleted data

    # retrieve and delete any pre-existing phone_number soft-deleted retention durations
    phone_number_rds = client.GetSoftDeletedRetentionDurationsOnColumn(
        phone_number.id,
    )
    for rd in phone_number_rds.retention_durations:
        if rd.id != uuid.UUID(int=0):
            client.DeleteSoftDeletedRetentionDurationOnColumn(phone_number.id, rd.id)

    # retain soft-deleted phone_number values with a support purpose for 3 months
    column_rd_update = UpdateColumnRetentionDurationsRequest(
        [
            ColumnRetentionDuration(
                duration_type="softdeleted",
                duration=RetentionDuration(unit="month", duration=3),
                column_id=phone_number.id,
                purpose_id=support.id,
            ),
        ],
    )
    client.UpdateSoftDeletedRetentionDurationsOnColumn(
        columnID=phone_number.id,
        req=column_rd_update,
    )

    # retrieve and delete pre-existing default soft-deleted retention duration on tenant
    try:
        default_duration = client.GetDefaultSoftDeletedRetentionDurationOnTenant()
        if default_duration.retention_duration.id != uuid.UUID(int=0):
            client.DeleteSoftDeletedRetentionDurationOnTenant(
                default_duration.retention_duration.id
            )
    except Error:
        pass

    # retain all soft-deleted values for any column or purpose for 1 week by default
    tenant_rd_update = UpdateColumnRetentionDurationRequest(
        ColumnRetentionDuration(
            duration_type="softdeleted",
            duration=RetentionDuration(unit="week", duration=1),
        ),
    )

    client.CreateSoftDeletedRetentionDurationOnTenant(
        tenant_rd_update,
    )

    # retrieve and delete any pre-existing security purpose soft-deleted retention duration
    try:
        purpose_rd = client.GetDefaultSoftDeletedRetentionDurationOnPurpose(
            security.id,
        )
        if purpose_rd.retention_duration.id != uuid.UUID(int=0):
            client.DeleteSoftDeletedRetentionDurationOnPurpose(
                security.id, purpose_rd.retention_duration.id
            )
    except Error:
        pass

    # retain soft-deleted values for any column with a security purpose for 1 year by default
    purpose_rd_update = UpdateColumnRetentionDurationRequest(
        ColumnRetentionDuration(
            duration_type="softdeleted",
            duration=RetentionDuration(unit="year", duration=1),
            purpose_id=security.id,
        ),
    )

    client.CreateSoftDeletedRetentionDurationOnPurpose(
        security.id,
        purpose_rd_update,
    )

    # retrieve phone_number soft-deleted retention durations after configuration
    phone_number_rds = client.GetSoftDeletedRetentionDurationsOnColumn(
        phone_number.id,
    )
    print(f"phone_number retention durations post-configuration: {phone_number_rds}\n")

    # Create an access policy that allows access to the data in the columns for security
    # and support purposes
    apt = AccessPolicyTemplate(
        name="PIIAccessPolicyTemplate",
        function="""function policy(context, params) {
            return params.teams.includes(context.client.team);
        }""",
    )
    apt = client.CreateAccessPolicyTemplate(apt, if_not_exists=True)

    ap = AccessPolicy(
        name="PIIAccessForSecurityandSupport",
        policy_type=POLICY_TYPE_COMPOSITE_INTERSECTION,
        components=[
            AccessPolicyComponent(
                template=ResourceID(name="PIIAccessPolicyTemplate"),
                template_parameters='{"teams": ["security_team", "support_team"]}',
            )
        ],
    )
    ap = client.CreateAccessPolicy(ap, if_not_exists=True)

    # Create a transformer that transforms the data in the columns for security and
    # support teams
    phone_transformer_function = r"""
function transform(data, params) {
    if (params.team == "security_team") {
        return data;
    } else if (params.team == "support_team") {
        phone = /^(\d{3})-(\d{3})-(\d{4})$/.exec(data);
        if (phone) {
            return "XXX-XXX-"+phone[3];
        } else {
            return "<invalid phone number>";
        }
    }
    return "";
}"""

    support_phone_transformer = Transformer(
        id=None,
        name="PIITransformerForSupport",
        input_type=DATA_TYPE_STRING,
        output_type=DATA_TYPE_STRING,
        reuse_existing_token=False,
        transform_type=TRANSFORM_TYPE_TRANSFORM,
        function=phone_transformer_function,
        parameters='{"team": "support_team"}',
    )
    support_phone_transformer = client.CreateTransformer(
        support_phone_transformer, if_not_exists=True
    )

    security_phone_transformer = Transformer(
        id=None,
        name="PIITransformerForSecurity",
        input_type=DATA_TYPE_STRING,
        output_type=DATA_TYPE_STRING,
        reuse_existing_token=False,
        transform_type=TRANSFORM_TYPE_TRANSFORM,
        function=phone_transformer_function,
        parameters='{"team": "security_team"}',
    )
    security_phone_transformer = client.CreateTransformer(
        security_phone_transformer, if_not_exists=True
    )

    phone_tokenizing_transformer_function = r"""
function id(len) {
        var s = "0123456789";
        return Array(len).join().split(',').map(function() {
            return s.charAt(Math.floor(Math.random() * s.length));
        }).join('');
    }
    function validate(str) {
        return (str.length === 10);
    }
    function transform(data, params) {
      // Strip non numeric characters if present
      orig_data = data;
      data = data.replace(/\D/g, '');
      if (data.length === 11 ) {
        data = data.substr(1, 11);
      }
      if (!validate(data)) {
            throw new Error('Invalid US Phone Number Provided');
      }
      return '1' + id(10);
}"""

    logging_phone_transformer = Transformer(
        id=None,
        name="PIITransformerForLogging",
        input_type=DATA_TYPE_STRING,
        output_type=DATA_TYPE_STRING,
        reuse_existing_token=True,  # Set this is to false to get a unique token every time this transformer is called vs getting same token on every call
        transform_type=TRANSFORM_TYPE_TOKENIZE_BY_VALUE,
        function=phone_tokenizing_transformer_function,
        parameters='{"team": "security_team"}',
    )

    logging_phone_transformer = client.CreateTransformer(
        logging_phone_transformer, if_not_exists=True
    )
    # Accessors are configurable APIs that allow a client to retrieve data from the user
    # store. Accessors are intended to be use-case specific. They enforce data usage
    # policies and minimize outbound data from the store for their given use case.

    # Selectors are used to filter the set of users that are returned by an accessor.
    # They are essentially SQL WHERE clauses and are configured per-accessor /
    # per-mutator referencing column IDs of the userstore.

    # Here we create accessors for two example teams: (1) security team and (2) support
    # team

    acc_support = Accessor(
        id=None,
        name="PIIAccessor-SupportTeam",
        description="Accessor for support team",
        columns=[
            ColumnOutputConfig(
                column=_PHONE_NUMBER_COLUMN_RESOURCE_ID,
                transformer=ResourceID(id=support_phone_transformer.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="home_addresses"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="created"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="id"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
        ],
        access_policy=ResourceID(id=ap.id),
        selector_config=UserSelectorConfig("{id} = ?"),
        purposes=[ResourceID(name="support")],
    )
    acc_support = client.CreateAccessor(acc_support, if_not_exists=True)

    # illustrate updating accessor, getting, and listing accessors
    acc_support.description = "New Name"
    acc_support = client.UpdateAccessor(acc_support)
    acc_support.description = "Accessor for support team"
    acc_support = client.UpdateAccessor(acc_support)
    acc_support = client.GetAccessor(acc_support.id)
    client.ListAccessors()

    acc_security = Accessor(
        id=None,
        name="PIIAccessor-SecurityTeam",
        description="Accessor for security team",
        columns=[
            ColumnOutputConfig(
                column=_PHONE_NUMBER_COLUMN_RESOURCE_ID,
                transformer=ResourceID(id=security_phone_transformer.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="home_addresses"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="created"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="id"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
        ],
        access_policy=ResourceID(id=ap.id),
        selector_config=UserSelectorConfig(
            "{home_addresses}->>'street_address_line_1' LIKE (?) AND "
            + "{phone_number} = (?)"
        ),
        purposes=[_SECURITY_PURPOSE_RESOURCE_ID],
    )
    acc_security = client.CreateAccessor(acc_security, if_not_exists=True)

    acc_marketing = Accessor(
        id=None,
        name="PIIAccessor-MarketingTeam",
        description="Accessor for marketing team",
        columns=[
            ColumnOutputConfig(
                column=_PHONE_NUMBER_COLUMN_RESOURCE_ID,
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="home_addresses"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="created"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
            ColumnOutputConfig(
                column=ResourceID(name="id"),
                transformer=ResourceID(id=TransformerPassThrough.id),
            ),
        ],
        access_policy=ResourceID(id=AccessPolicyOpen.id),
        selector_config=UserSelectorConfig("{id} = ?"),
        purposes=[_SECURITY_PURPOSE_RESOURCE_ID],
    )
    acc_marketing = client.CreateAccessor(acc_marketing, if_not_exists=True)

    acc_logging = Accessor(
        id=None,
        name="PhoneTokenAccessorForSecurityTeam",
        description="Accessor for getting phone number token for security team",
        columns=[
            ColumnOutputConfig(
                column=_PHONE_NUMBER_COLUMN_RESOURCE_ID,
                transformer=ResourceID(id=logging_phone_transformer.id),
            ),
        ],
        access_policy=ResourceID(id=AccessPolicyOpen.id),
        selector_config=UserSelectorConfig("{id} = ?"),
        purposes=[_SECURITY_PURPOSE_RESOURCE_ID],
        token_access_policy=ResourceID(id=AccessPolicyOpen.id),
    )
    acc_logging = client.CreateAccessor(acc_logging, if_not_exists=True)

    # Mutators are configurable APIs that allow a client to write data to the User
    # Store. Mutators (setters) can be thought of as the complement to accessors
    # (getters). Here we create mutator to update the user's phone number and home
    # address, and another mutator for updating email address.
    phone_address_mutator = Mutator(
        id=None,
        name="PhoneAndAddressMutator",
        description="Mutator for updating phone number and home address",
        columns=[
            ColumnInputConfig(
                column=_PHONE_NUMBER_COLUMN_RESOURCE_ID,
                validator=ResourceID(id=ValidatorOpen.id),
            ),
            ColumnInputConfig(
                column=ResourceID(name="home_addresses"),
                validator=ResourceID(id=ValidatorOpen.id),
            ),
        ],
        access_policy=ResourceID(id=AccessPolicyOpen.id),
        selector_config=UserSelectorConfig("{id} = ?"),
    )
    phone_address_mutator = client.CreateMutator(
        phone_address_mutator, if_not_exists=True
    )
    # illustrate updating, getting, and listing mutators
    phone_address_mutator.description = "New description"
    phone_address_mutator = client.UpdateMutator(phone_address_mutator)
    phone_address_mutator.description = (
        "Mutator for updating phone number and home address"
    )
    phone_address_mutator = client.UpdateMutator(phone_address_mutator)
    phone_address_mutator = client.GetMutator(phone_address_mutator.id)
    client.ListMutators()

    email_mutator = Mutator(
        id=None,
        name="EmailMutator",
        description="Mutator for updating email",
        columns=[
            ColumnInputConfig(
                column=_EMAIL_COLUMN_RESOURCE_ID,
                validator=ResourceID(id=ValidatorOpen.id),
            ),
        ],
        access_policy=ResourceID(id=AccessPolicyOpen.id),
        selector_config=UserSelectorConfig("{id} = ?"),
    )
    email_mutator = client.CreateMutator(email_mutator, if_not_exists=True)

    return (
        acc_support,
        acc_security,
        acc_marketing,
        acc_logging,
        phone_address_mutator,
        email_mutator,
    )


def example(
    client: Client,
    acc_support: Accessor,
    acc_security: Accessor,
    acc_marketing: Accessor,
    acc_logging: Accessor,
    phone_address_mutator: Mutator,
    email_mutator: Mutator,
):
    email = "me@example.org"

    # delete any existing test users with the email address for their AuthN
    users = client.ListUsers(email=email)
    for user in users:
        client.DeleteUser(user.id)

    # create a user
    uid = client.CreateUser()

    # retrieve the user the "old way" (not using accessors) just for illustration
    user = client.GetUser(uid)

    # update the user using the "old way" (not using mutators) just for illustration
    profile = user.profile
    profile[_EMAIL_COLUMN_NAME] = email
    profile[_PHONE_NUMBER_COLUMN_NAME] = "123-456-7890"
    client.UpdateUser(uid, profile)

    # retrieve the user the "old way" (not using accessors) just for illustration
    user = client.GetUser(uid)
    print(f"old way: user's details are {user.profile}\n")

    client.DeleteUser(uid)

    # create and initialize a user with email address
    uid = client.CreateUserWithMutator(
        mutator_id=email_mutator.id,
        context={},
        row_data={
            "email": {
                "value": email,
                "purpose_additions": [
                    {"Name": "operational"},
                ],
            },
        },
    )

    # set the user's info using the mutator
    client.ExecuteMutator(
        mutator_id=phone_address_mutator.id,
        context={},
        selector_values=[uid],
        row_data={
            _PHONE_NUMBER_COLUMN_NAME: {
                "value": "123-456-7890",
                "purpose_additions": [
                    {"Name": _SECURITY_PURPOSE_NAME},
                    {"Name": "support"},
                    {"Name": "operational"},
                ],
            },
            "home_addresses": {
                "value": '[{"country":"usa", "street_address_line_1":"742 Evergreen \
Terrace", "locality":"Springfield"}, {"country":"usa", "street_address_line_1":"123 \
Main St", "locality":"Pleasantville"}]',
                "purpose_additions": [
                    {"Name": _SECURITY_PURPOSE_NAME},
                    {"Name": "support"},
                    {"Name": "operational"},
                ],
            },
        },
    )

    # now retrieve the user's info using the accessor with the right context
    resolved = client.ExecuteAccessor(
        accessor_id=acc_support.id,
        context={"team": "support_team"},
        selector_values=[uid],
    )
    # expect ['["XXX-XXX-7890","<home address hidden>"]']
    print(f"support context: user's details are {resolved}\n")

    resolved = client.ExecuteAccessor(
        accessor_id=acc_security.id,
        context={"team": "security_team"},
        selector_values=["%Evergreen%", "123-456-7890"],
    )
    # expect full details
    print(f"security context: user's details are {resolved}\n")

    resolved = client.ExecuteAccessor(
        accessor_id=acc_marketing.id,
        context={"team": "marketing_team"},
        selector_values=[uid],
    )
    # expect [] (due to team mismatch in access policy)
    print(f"marketing context: user's details are {resolved}\n")

    resolved = client.ExecuteAccessor(
        accessor_id=acc_logging.id,
        context={"team": "security_team"},
        selector_values=[uid],
    )
    # expect to get back a token
    token = json.loads(resolved["data"][0])[_PHONE_NUMBER_COLUMN_NAME]
    print(f"user's phone token (first call) {token}\n")

    resolved = client.ExecuteAccessor(
        accessor_id=acc_logging.id,
        context={"team": "security_team"},
        selector_values=[uid],
    )

    # expect to get back the same token so it can be used in logs as a unique identifier if desired
    token = json.loads(resolved["data"][0])[_PHONE_NUMBER_COLUMN_NAME]
    print(f"user's phone token (repeat call) {token}\n")

    # resolving the token to the original phone number
    value = client.ResolveTokens(
        [token], {"team": "security_team"}, [_SECURITY_PURPOSE_RESOURCE_ID]
    )
    print(f"user's phone token resolved  {value}\n")

    client.DeleteUser(uid)


def cleanup(
    client: Client,
    acc_support: Accessor,
    acc_security: Accessor,
    acc_marketing: Accessor,
    acc_logging: Accessor,
    phone_address_mutator: Mutator,
    email_mutator: Mutator,
):
    # delete the accessors and mutators
    client.DeleteAccessor(acc_support.id)
    client.DeleteAccessor(acc_security.id)
    client.DeleteAccessor(acc_marketing.id)
    client.DeleteAccessor(acc_logging.id)
    client.DeleteMutator(phone_address_mutator.id)
    client.DeleteMutator(email_mutator.id)

    # delete the created retention durations
    clean_retention_durations(client)


def clean_retention_durations(client: Client) -> None:
    column_id = next(
        (
            col.id
            for col in client.ListColumns()
            if col.name == _PHONE_NUMBER_COLUMN_NAME
        ),
        None,
    )
    purpose_id = next(
        (
            purpose.id
            for purpose in client.ListPurposes()
            if purpose.name == _SECURITY_PURPOSE_NAME
        ),
        None,
    )

    if column_id:
        created_rds = client.GetSoftDeletedRetentionDurationsOnColumn(
            column_id
        ).retention_durations
    else:
        created_rds: list[RetentionDuration] = []
        warnings.warn(f"Failed to find column - {_PHONE_NUMBER_COLUMN_NAME}")
    created_rds.append(
        client.GetDefaultSoftDeletedRetentionDurationOnTenant().retention_duration
    )
    if purpose_id:
        created_rds.append(
            client.GetDefaultSoftDeletedRetentionDurationOnPurpose(
                purpose_id
            ).retention_duration
        )
    else:
        warnings.warn(f"Failed to find purpose - {_SECURITY_PURPOSE_NAME}")

    for rd in created_rds:
        if rd.id == uuid.UUID(int=0):
            continue
        if rd.column_id == uuid.UUID(int=0):
            if rd.purpose_id == uuid.UUID(int=0):
                if not client.DeleteSoftDeletedRetentionDurationOnTenant(rd.id):
                    warnings.warn(
                        f"Failed to delete default retention duration on tenant - {rd.id=}"
                    )
            else:
                if not client.DeleteSoftDeletedRetentionDurationOnPurpose(
                    rd.purpose_id, rd.id
                ):
                    warnings.warn(
                        f"Failed to delete default retention duration on purpose - {rd.id=} - {rd.purpose_id=}"
                    )
        else:
            if not client.DeleteSoftDeletedRetentionDurationOnColumn(
                rd.column_id, rd.id
            ):
                warnings.warn(
                    f"Failed to delete default retention duration on column - {rd.id=} - {rd.column_id=}"
                )


def run_userstore_sample(client: Client) -> None:
    # set up the userstore with the right columns, policies, accessors, mutators,
    # and retention durations
    (
        acc_support,
        acc_security,
        acc_marketing,
        acc_logging,
        phone_address_mutator,
        email_mutator,
    ) = setup(client)
    # run the example
    example(
        client,
        acc_support,
        acc_security,
        acc_marketing,
        acc_logging,
        phone_address_mutator,
        email_mutator,
    )
    cleanup(
        client,
        acc_support,
        acc_security,
        acc_marketing,
        acc_logging,
        phone_address_mutator,
        email_mutator,
    )


if __name__ == "__main__":
    disable_ssl_verify = (
        os.environ.get("DEV_ONLY_DISABLE_SSL_VERIFICATION", "") == "true"
    )
    client = (
        Client(url, client_id, client_secret, verify=False)
        if disable_ssl_verify
        else Client(url, client_id, client_secret)
    )
    run_userstore_sample(client)
