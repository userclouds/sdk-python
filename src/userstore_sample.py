import uuid

from usercloudssdk.client import Client
from usercloudssdk.constants import (
    COLUMN_INDEX_TYPE_INDEXED,
    COLUMN_INDEX_TYPE_NONE,
    DATA_TYPE_ADDRESS,
    DATA_TYPE_BOOLEAN,
    DATA_TYPE_STRING,
    POLICY_TYPE_COMPOSITE_INTERSECTION,
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


def setup(c: Client):
    # illustrate CRUD for columns
    col = c.CreateColumn(
        Column(
            None,
            "temp_column",
            DATA_TYPE_BOOLEAN,
            False,
            "",
            COLUMN_INDEX_TYPE_NONE,
        ),
        if_not_exists=True,
    )
    c.ListColumns()
    col = c.GetColumn(col.id)
    col.name = "temp_column_renamed"
    c.UpdateColumn(col)
    c.DeleteColumn(col.id)

    # create phone number and home address columns
    phone_number = c.CreateColumn(
        Column(
            None,
            "phone_number",
            DATA_TYPE_STRING,
            False,
            "",
            COLUMN_INDEX_TYPE_INDEXED,
        ),
        if_not_exists=True,
    )

    c.CreateColumn(
        Column(
            None,
            "home_addresses",
            DATA_TYPE_ADDRESS,
            True,
            "",
            COLUMN_INDEX_TYPE_NONE,
        ),
        if_not_exists=True,
    )

    # illustrate CRUD for purposes
    purpose = c.CreatePurpose(
        Purpose(None, "temp_purpose", "temp_purpose_description"), if_not_exists=True
    )
    c.ListPurposes()
    purpose = c.GetPurpose(purpose.id)
    purpose.description = "new description"
    c.UpdatePurpose(purpose)
    c.DeletePurpose(purpose.id)

    # create purposes for security, support and marketing
    security = c.CreatePurpose(
        Purpose(
            None,
            "security",
            "Allows access to the data in the columns for security purposes",
        ),
        if_not_exists=True,
    )

    support = c.CreatePurpose(
        Purpose(
            None,
            "support",
            "Allows access to the data in the columns for support purposes",
        ),
        if_not_exists=True,
    )

    c.CreatePurpose(
        Purpose(
            None,
            "marketing",
            "Allows access to the data in the columns for marketing purposes",
        ),
        if_not_exists=True,
    )

    # configure retention durations for soft-deleted data

    # retrieve phone_number soft-deleted retention durations
    phone_number_rds = c.GetSoftDeletedRetentionDurationsOnColumn(
        phone_number.id,
    )
    print(f"phone_number retention durations pre-configuration: {phone_number_rds}\n")

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
    created_rds = c.UpdateSoftDeletedRetentionDurationsOnColumn(
        phone_number.id,
        column_rd_update,
    ).retention_durations

    # retain all soft-deleted values for any column or purpose for 1 week by default
    tenant_rd_update = UpdateColumnRetentionDurationRequest(
        ColumnRetentionDuration(
            duration_type="softdeleted",
            duration=RetentionDuration(unit="week", duration=1),
        ),
    )
    created_rds.append(
        c.CreateSoftDeletedRetentionDurationOnTenant(
            tenant_rd_update,
        ).retention_duration
    )

    # retain soft-deleted values for any column with a security purpose for 1 year by default
    purpose_rd_update = UpdateColumnRetentionDurationRequest(
        ColumnRetentionDuration(
            duration_type="softdeleted",
            duration=RetentionDuration(unit="year", duration=1),
            purpose_id=security.id,
        ),
    )
    created_rds.append(
        c.CreateSoftDeletedRetentionDurationOnPurpose(
            security.id,
            purpose_rd_update,
        ).retention_duration
    )

    # retrieve phone_number soft-deleted retention durations after configuration
    phone_number_rds = c.GetSoftDeletedRetentionDurationsOnColumn(
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
    apt = c.CreateAccessPolicyTemplate(apt, if_not_exists=True)

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
    ap = c.CreateAccessPolicy(ap, if_not_exists=True)

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
        None,
        "PIITransformerForSupport",
        DATA_TYPE_STRING,
        TRANSFORM_TYPE_TRANSFORM,
        phone_transformer_function,
        '{"team": "support_team"}',
    )
    support_phone_transformer = c.CreateTransformer(
        support_phone_transformer, if_not_exists=True
    )

    security_phone_transformer = Transformer(
        None,
        "PIITransformerForSecurity",
        DATA_TYPE_STRING,
        TRANSFORM_TYPE_TRANSFORM,
        phone_transformer_function,
        '{"team": "security_team"}',
    )
    security_phone_transformer = c.CreateTransformer(
        security_phone_transformer, if_not_exists=True
    )

    # Accessors are configurable APIs that allow a client to retrieve data from the user
    # store. Accessors are intended to be use-case specific. They enforce data usage
    # policies and minimize outbound data from the store for their given use case.

    # Selectors are used to filter the set of users that are returned by an accessor.
    # They are eseentially SQL WHERE clauses and are configured per-accessor /
    # per-mutator referencing column IDs of the userstore.

    # Here we create accessors for two example teams: (1) security team and (2) support
    # team

    acc_support = Accessor(
        None,
        "PIIAccessor-SupportTeam",
        "New Accessor",
        [
            ColumnOutputConfig(
                column=ResourceID(name="phone_number"),
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
        ResourceID(id=ap.id),
        UserSelectorConfig("{id} = ?"),
        [ResourceID(name="support")],
    )
    acc_support = c.CreateAccessor(acc_support, if_not_exists=True)
    acc_support.description = "Accessor for support team"
    acc_support = c.UpdateAccessor(acc_support)
    acc_support = c.GetAccessor(acc_support.id)
    c.ListAccessors()

    acc_security = Accessor(
        None,
        "PIIAccessor-SecurityTeam",
        "Accessor for security team",
        [
            ColumnOutputConfig(
                column=ResourceID(name="phone_number"),
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
        ResourceID(id=ap.id),
        UserSelectorConfig(
            "{home_addresses}->>'street_address_line_1' LIKE (?) AND "
            + "{phone_number} = (?)"
        ),
        [ResourceID(name="security")],
    )
    acc_security = c.CreateAccessor(acc_security, if_not_exists=True)

    acc_marketing = Accessor(
        None,
        "PIIAccessor-MarketingTeam",
        "Accessor for marketing team",
        [
            ColumnOutputConfig(
                column=ResourceID(name="phone_number"),
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
        ResourceID(id=AccessPolicyOpen.id),
        UserSelectorConfig("{id} = ?"),
        [ResourceID(name="marketing")],
    )
    acc_marketing = c.CreateAccessor(acc_marketing, if_not_exists=True)

    # Mutators are configurable APIs that allow a client to write data to the User
    # Store. Mutators (setters) can be thought of as the complement to accessors
    # (getters). Here we create mutator to update the user's phone number and home
    # address.
    mutator = Mutator(
        None,
        "PhoneAndAddressMutator",
        "New mutator",
        [
            ColumnInputConfig(
                column=ResourceID(name="phone_number"),
                validator=ResourceID(id=ValidatorOpen.id),
            ),
            ColumnInputConfig(
                column=ResourceID(name="home_addresses"),
                validator=ResourceID(id=ValidatorOpen.id),
            ),
        ],
        ResourceID(id=AccessPolicyOpen.id),
        UserSelectorConfig("{id} = ?"),
    )
    mutator = c.CreateMutator(mutator, if_not_exists=True)
    mutator.description = "Mutator for updating phone number and home address"
    mutator = c.UpdateMutator(mutator)
    mutator = c.GetMutator(mutator.id)
    c.ListMutators()

    return acc_support, acc_security, acc_marketing, mutator, created_rds


def example(
    c: Client,
    acc_support: Accessor,
    acc_security: Accessor,
    acc_marketing: Accessor,
    mutator: Mutator,
):
    email = "me@example.org"

    # delete any existing test users with the email address or external alias
    users = c.ListUsers(email=email)
    for user in users:
        c.DeleteUser(user.id)

    # create a user
    uid = c.CreateUser()

    # retrieve the user the "old way" (not using accessors) just for illustration
    user = c.GetUser(uid)

    # update the user using the "old way" (not using mutators) just for illustration
    profile = user.profile
    profile["phone_number"] = "123-456-7890"
    c.UpdateUser(uid, profile)

    # retrieve the user the "old way" (not using accessors) just for illustration
    user = c.GetUser(uid)
    print(f"old way: user's details are {user.profile}\n")

    # set the user's info using the mutator
    c.ExecuteMutator(
        mutator.id,
        {},
        [uid],
        {
            "phone_number": {
                "value": "123-456-7890",
                "purpose_additions": [
                    {"Name": "security"},
                    {"Name": "support"},
                    {"Name": "operational"},
                ],
            },
            "home_addresses": {
                "value": '[{"country":"usa", "street_address_line_1":"742 Evergreen \
Terrace", "locality":"Springfield"}, {"country":"usa", "street_address_line_1":"123 \
Main St", "locality":"Pleasantville"}]',
                "purpose_additions": [
                    {"Name": "security"},
                    {"Name": "support"},
                    {"Name": "operational"},
                ],
            },
        },
    )

    # now retrieve the user's info using the accessor with the right context
    resolved = c.ExecuteAccessor(acc_support.id, {"team": "support_team"}, [uid])
    # expect ['["XXX-XXX-7890","<home address hidden>"]']
    print(f"support context: user's details are {resolved}\n")

    resolved = c.ExecuteAccessor(
        acc_security.id,
        {"team": "security_team"},
        ["%Evergreen%", "123-456-7890"],
    )
    # expect full details
    print(f"security context: user's details are {resolved}\n")

    resolved = c.ExecuteAccessor(
        acc_marketing.id,
        {"team": "marketing_team"},
        [uid],
    )
    # expect [] (due to team mismatch in access policy)
    print(f"marketing context: user's details are {resolved}\n")

    c.DeleteUser(uid)


def cleanup(
    c: Client,
    acc_support: Accessor,
    acc_security: Accessor,
    acc_marketing: Accessor,
    mutator: Mutator,
    created_rds: list[ColumnRetentionDuration],
):
    # delete the accessors and mutators
    c.DeleteAccessor(acc_support.id)
    c.DeleteAccessor(acc_security.id)
    c.DeleteAccessor(acc_marketing.id)
    c.DeleteMutator(mutator.id)

    # delete the created retention durations
    for rd in created_rds:
        if rd.column_id == uuid.UUID(int=0):
            if rd.purpose_id == uuid.UUID(int=0):
                c.DeleteSoftDeletedRetentionDurationOnTenant(rd.id)
            else:
                c.DeleteSoftDeletedRetentionDurationOnPurpose(rd.purpose_id, rd.id)
        else:
            c.DeleteSoftDeletedRetentionDurationOnColumn(rd.column_id, rd.id)


def run_userstore_sample(c: Client) -> None:
    # set up the userstore with the right columns, policies, accessors, mutators,
    # and retention durations
    acc_support, acc_security, acc_marketing, mutator, created_rds = setup(c)
    # run the example
    example(c, acc_support, acc_security, acc_marketing, mutator)
    cleanup(c, acc_support, acc_security, acc_marketing, mutator, created_rds)


if __name__ == "__main__":
    c = Client(url, client_id, client_secret)
    run_userstore_sample(c)
