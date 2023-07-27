import functools
import sys
import uuid

from usercloudssdk.client import Client, Error
from usercloudssdk.models import (
    AccessPolicy,
    Transformer,
    AccessPolicyComponent,
    AccessPolicyTemplate,
    ResourceID,
)
from usercloudssdk.policies import AccessPolicyOpen, TransformerUUID
from usercloudssdk.constants import (
    POLICY_TYPE_COMPOSITE_INTERSECTION,
    DATA_TYPE_STRING,
    TRANSFORM_TYPE_TRANSFORM,
)

client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"


def test_access_policies(c: Client):
    new_apt = AccessPolicyTemplate(
        name="test_template",
        function=f"function policy(x, y) {{ return false /* {id} */}};",
    )

    try:
        created_apt = c.CreateAccessPolicyTemplate(new_apt, if_not_exists=True)
    except Error as e:
        print("failed to create new access policy template: ", e)
        sys.exit(1)

    new_ap = AccessPolicy(
        name="test_access_policy",
        policy_type=POLICY_TYPE_COMPOSITE_INTERSECTION,
        components=[
            AccessPolicyComponent(
                template=ResourceID(name="test_template"), template_parameters="{}"
            )
        ],
    )

    try:
        created_ap = c.CreateAccessPolicy(new_ap, if_not_exists=True)
    except Error as e:
        print("failed to create new access policy: ", e)
        sys.exit(1)

    aps = []
    try:
        aps = c.ListAccessPolicies()
    except Error as e:
        print("failed to list access policies: ", e)

    if not functools.reduce(
        lambda found, ap: found or (ap.id == AccessPolicyOpen.id), aps
    ):
        print("missing AccessPolicyOpen in list: ", aps)
    if not functools.reduce(lambda found, ap: found or (ap.id == created_ap.id), aps):
        print("missing new access policy in list: ", aps)

    created_ap.components[0].template_parameters = '{"foo": "bar"}'

    try:
        update = c.UpdateAccessPolicy(created_ap)
        if update.version != created_ap.version + 1:
            print(
                f"update changed version from {created_ap.version} to {update.version}, expected +1"
            )
    except Error as e:
        print("failed to update access policy: ", e)

    try:
        if not c.DeleteAccessPolicy(update.id, update.version):
            print("failed to delete access policy but no error?")
    except Error as e:
        print("failed to delete access policy: ", e)

    try:
        aps = c.ListAccessPolicies()
        for ap in aps:
            if ap.id == update.id:
                if ap.version != 0:
                    print(f"got access policy with version {ap.version}, expected 0")
        if len(aps) == 0:
            print(f"found no policies, expected to find version 0")
    except Error as e:
        print("failed to get access policy: ", e)

    # clean up the original AP and Template so you can re-run the sample repeatedly without an error
    try:
        if not c.DeleteAccessPolicy(update.id, 0):
            print("failed to delete access policy but no error?")
    except Error as e:
        print("failed to delete access policy: ", e)

    try:
        if not c.DeleteAccessPolicyTemplate(created_apt.id, 0):
            print("failed to delete access policy template but no error?")
    except Error as e:
        print("failed to delete access policy template: ", e)


def test_transformers(c: Client):
    new_gp = Transformer(
        name="test_transformer",
        input_type=DATA_TYPE_STRING,
        transform_type=TRANSFORM_TYPE_TRANSFORM,
        function=f"function transform(x, y) {{ return 'token' }};",
        parameters="{}",
    )

    try:
        created_gp = c.CreateTransformer(new_gp, if_not_exists=True)
    except Error as e:
        print("failed to create new transformer: ", e)

    gps = []
    try:
        gps = c.ListTransformers()
    except Error as e:
        print("failed to list transformers: ", e)

    if not functools.reduce(
        lambda found, gp: found or (gp.id == TransformerUUID.id), gps
    ):
        print("missing TransformerUUID in list: ", gps)
    if not functools.reduce(lambda found, gp: found or (gp.id == created_gp.id), gps):
        print("missing new transformer in list: ", gps)

    try:
        if not c.DeleteTransformer(created_gp.id):
            print("failed to delete transformer but no error?")
    except Error as e:
        print("failed to delete transformer: ", e)


def test_token_apis(c: Client):
    originalData = "something very secret"
    token = c.CreateToken(originalData, TransformerUUID, AccessPolicyOpen)
    print(f"Token: {token}")

    resp = c.ResolveTokens([token], {}, [])
    if len(resp) != 1 or resp[0]["data"] != originalData:
        print("something went wrong")
    else:
        print(f"Data: {resp[0]['data']}")

    lookup_tokens = None
    try:
        lookup_tokens = c.LookupToken(originalData, TransformerUUID, AccessPolicyOpen)
    except Error as e:
        print("failed to lookup token: ", e)

    if token not in lookup_tokens:
        print(
            f"expected lookup tokens {lookup_tokens} to contain created token {token}"
        )

    itr = None
    try:
        itr = c.InspectToken(token)
    except Error as e:
        print("failed to inspect token: ", e)

    if itr.token != token:
        print(f"expected inspect token {itr.token} to match created token {token}")
    if itr.transformer.id != TransformerUUID.id:
        print(
            f"expected inspect transformer {itr.transformer.id} to match created transformer {TransformerUUID.id}"
        )
    if itr.access_policy.id != AccessPolicyOpen.id:
        print(
            f"expected inspect access policy {itr.access_policy.id} to match created access policy {AccessPolicyOpen.id}"
        )

    try:
        if not c.DeleteToken(token):
            print("failed to delete token but no error?")
    except Error as e:
        print("failed to delete token: ", e)


def test_error_handling(c):
    try:
        d = c.ResolveTokens(["not a token"], {}, [])
        print("expected error but got data: ", d)
    except Error as e:
        if e.code != 404:
            print("got unexpected error code (wanted 404): ", e.code)


if __name__ == "__main__":
    c = Client(url, client_id, client_secret)

    test_access_policies(c)
    test_transformers(c)
    test_token_apis(c)
    test_error_handling(c)
