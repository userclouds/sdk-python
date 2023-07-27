import uuid

from usercloudssdk.client import Client, Error
from usercloudssdk.models import (
    AccessPolicy,
    AccessPolicyTemplate,
    AccessPolicyComponent,
    Column,
    ColumnInputConfig,
    ColumnOutputConfig,
    Accessor,
    Mutator,
    Purpose,
    ResourceID,
    UserSelectorConfig,
    Transformer,
)
from usercloudssdk.constants import (
    DATA_TYPE_STRING,
    DATA_TYPE_ADDRESS,
    COLUMN_INDEX_TYPE_NONE,
    COLUMN_INDEX_TYPE_INDEXED,
    POLICY_TYPE_COMPOSITE_INTERSECTION,
    TRANSFORM_TYPE_TRANSFORM,
)
from usercloudssdk.policies import (
    AccessPolicyOpen,
    ValidatorOpen,
    TransformerPassThrough,
)

client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"


# This sample shows you how to create new columns in the user store and create access policies governing access
# to the data inside those columns. It also shows you how to create, delete and execute accessors and mutators.
# To learn more about these concepts, see documentation.userclouds.com.


def setup(c: Client):

    # create phone number and home address columns
    c.CreateColumn(
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

    c.CreatePurpose(
        Purpose(
            None,
            "security",
            "Allows access to the data in the columns for security purposes",
        ),
        if_not_exists=True,
    )

    c.CreatePurpose(
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

    # Create an access policy that allows access to the data in the columns for security and support purposes
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

    # Create a transformer that transforms the data in the columns for security and support teams
    phone_transformer_function = """
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

    # Accessors are configurable APIs that allow a client to retrieve data from the user store. Accessors are
    # intended to be use-case specific. They enforce data usage policies and minimize outbound data from the
    # store for their given use case.

    # Selectors are used to filter the set of users that are returned by an accessor. They are eseentially SQL
    # WHERE clauses and are configured per-accessor / per-mutator referencing column IDs of the userstore.

    # Here we create accessors for two example teams: (1) security team and (2) support team
    acc_support = Accessor(
        None,
        "PIIAccessor-SupportTeam",
        "Accessor for support team",
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
            "{home_addresses}->>'street_address_line_1' LIKE (?) AND {phone_number} = (?)"
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

    # Mutators are configurable APIs that allow a client to write data to the User Store. Mutators (setters)
    # can be thought of as the complement to accessors (getters). Here we create mutator to update the user's
    # phone number and home address
    mutator = Mutator(
        None,
        "PhoneAndAddressMutator",
        "Mutator for updating phone number and home address",
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

    return acc_support, acc_security, acc_marketing, mutator


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
                "value": """[{"country":"usa", "street_address_line_1":"742 Evergreen Terrace", "locality":"Springfield"},
                             {"country":"usa", "street_address_line_1":"123 Main St", "locality":"Pleasantville"}]""",
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
    print(f"support context: user's details are {resolved}")

    resolved = c.ExecuteAccessor(
        acc_security.id,
        {"team": "security_team"},
        ["%Evergreen%", "123-456-7890"],
    )
    # expect full details
    print(f"security context: user's details are {resolved}")

    resolved = c.ExecuteAccessor(
        acc_marketing.id,
        {"team": "marketing_team"},
        [uid],
    )
    # expect [] (due to team mismatch in access policy)
    print(f"marketing context: user's details are {resolved}")

    c.DeleteUser(uid)


if __name__ == "__main__":
    c = Client(url, client_id, client_secret)

    # set up the userstore with the right columns, policies, accessors and mutators
    acc_support, acc_security, acc_marketing, mutator = setup(c)

    # run the example
    example(c, acc_support, acc_security, acc_marketing, mutator)
