import base64
import time
import uuid
import urllib.parse

import jwt
import requests

from .models import (
    Accessor,
    AccessPolicy,
    AccessPolicyTemplate,
    APIErrorResponse,
    Column,
    InspectTokenResponse,
    Mutator,
    Purpose,
    ResourceID,
    UserResponse,
    Transformer,
)
from .constants import AUTHN_TYPE_PASSWORD
from . import ucjson


class Error(BaseException):
    def __init__(self, error="unspecified error", code=500, request_id=None):
        self.error = error
        self.code = code
        self.request_id = request_id

    def __repr__(self):
        return f"Error({self.error}, {self.code}, {self.request_id})"

    @staticmethod
    def from_json(j):
        return Error(j["error"], j["request_id"])


class Client:
    url: str
    client_id: str
    _client_secret: str

    _access_token: str

    def __init__(self, url, id, secret):
        self.url = url
        self.client_id = urllib.parse.quote(id)
        self._client_secret = urllib.parse.quote(secret)

        self._access_token = self._get_access_token()

    # User Operations

    def CreateUser(self) -> uuid.UUID:
        body = {}

        j = self._post("/authn/users", data=ucjson.dumps(body))
        return j.get("id")

    def CreateUserWithPassword(self, username: str, password: str) -> uuid.UUID:
        body = {
            "username": username,
            "password": password,
            "authn_type": AUTHN_TYPE_PASSWORD,
        }

        j = self._post("/authn/users", data=ucjson.dumps(body))
        return j.get("id")

    def ListUsers(
        self, limit: int = 0, starting_after: uuid.UUID = None, email: str = None
    ) -> list[UserResponse]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{str(starting_after)}"
        if email is not None:
            params["email"] = email
        params["version"] = "2"
        j = self._get("/authn/users", params=params)
        users = [UserResponse.from_json(ur) for ur in j["data"]]
        return users

    def GetUser(self, id: uuid.UUID) -> UserResponse:
        j = self._get(f"/authn/users/{str(id)}")
        return UserResponse.from_json(j)

    def UpdateUser(self, id: uuid.UUID, profile: dict) -> UserResponse:
        body = {"profile": profile}

        j = self._put(f"/authn/users/{str(id)}", data=ucjson.dumps(body))
        return UserResponse.from_json(j)

    def DeleteUser(self, id: uuid.UUID) -> bool:
        return self._delete(f"/authn/users/{str(id)}")

    # Column Operations

    def CreateColumn(self, column: Column, if_not_exists=False) -> Column:
        body = {"column": column.__dict__}

        try:
            j = self._post("/userstore/config/columns", data=ucjson.dumps(body))
            return Column.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    column.id = er.id
                    return column
            raise e

    def DeleteColumn(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/columns/{str(id)}")

    def GetColumn(self, id: uuid.UUID) -> Column:
        j = self._get(f"/userstore/config/columns/{str(id)}")
        return Column.from_json(j)

    def ListColumns(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Column]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{str(starting_after)}"
        params["version"] = "2"
        j = self._get("/userstore/config/columns", params=params)
        columns = [Column.from_json(c) for c in j["data"]]
        return columns

    def UpdateColumn(self, column: Column) -> Column:
        body = {"column": column.__dict__}

        j = self._put(f"/userstore/config/columns/{column.id}", data=ucjson.dumps(body))
        return Column.from_json(j)

    # Purpose Operations

    def CreatePurpose(self, purpose: Purpose, if_not_exists=False) -> Purpose:
        body = {"purpose": purpose.__dict__}

        try:
            j = self._post("/userstore/config/purposes", data=ucjson.dumps(body))
            return Purpose.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    purpose.id = er.id
                    return purpose
            raise e

    def DeletePurpose(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/purposes/{str(id)}")

    def GetPurpose(self, id: uuid.UUID) -> Purpose:
        j = self._get(f"/userstore/config/purposes/{str(id)}")
        return Purpose.from_json(j)

    def ListPurposes(self) -> list[Purpose]:
        j = self._get("/userstore/config/purposes")

        purposes = []
        for p in j:
            purposes.append(Purpose.from_json(p))

        return purposes

    def UpdatePurpose(self, purpose: Purpose) -> Purpose:
        body = {"purpose": purpose.__dict__}

        j = self._put(
            f"/userstore/config/purposes/{purpose.id}", data=ucjson.dumps(body)
        )
        return Purpose.from_json(j)

    # Access Policy Templates

    # Access Policies

    def CreateAccessPolicyTemplate(
        self, access_policy_template: AccessPolicyTemplate, if_not_exists=False
    ) -> AccessPolicyTemplate | Error:
        body = {"access_policy_template": access_policy_template.__dict__}

        try:
            j = self._post(
                "/tokenizer/policies/accesstemplate", data=ucjson.dumps(body)
            )
            return AccessPolicyTemplate.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    access_policy_template.id = er.id
                    return access_policy_template
            raise e

    def ListAccessPolicyTemplates(self):
        j = self._get("/tokenizer/policies/accesstemplate")

        policies = []
        for p in j["data"]:
            policies.append(AccessPolicyTemplate.from_json(p))

        return policies

    def GetAccessPolicyTemplate(self, rid: ResourceID):
        if rid.id is not None:
            j = self._get(f"/tokenizer/policies/accesstemplate/{str(rid.id)}")
        elif rid.name is not None:
            j = self._get(f"/tokenizer/policies/accesstemplate?name={rid.name}")

        return AccessPolicyTemplate.from_json(j)

    def UpdateAccessPolicyTemplate(self, access_policy_template: AccessPolicyTemplate):
        body = {"access_policy_template": access_policy_template.__dict__}

        j = self._put(
            f"/tokenizer/policies/accesstemplate/{access_policy_template.id}",
            data=ucjson.dumps(body),
        )
        return AccessPolicyTemplate.from_json(j)

    def DeleteAccessPolicyTemplate(self, id: uuid.UUID, version: int):
        body = {"version": version}

        return self._delete(
            f"/tokenizer/policies/accesstemplate/{str(id)}", data=ucjson.dumps(body)
        )

    # Access Policies

    def CreateAccessPolicy(
        self, access_policy: AccessPolicy, if_not_exists=False
    ) -> AccessPolicy | Error:
        body = {"access_policy": access_policy.__dict__}

        try:
            j = self._post("/tokenizer/policies/access", data=ucjson.dumps(body))
            return AccessPolicy.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    access_policy.id = er.id
                    return access_policy
            raise e

    def ListAccessPolicies(self):
        j = self._get("/tokenizer/policies/access")

        policies = []
        for p in j["data"]:
            policies.append(AccessPolicy.from_json(p))

        return policies

    def GetAccessPolicy(self, rid: ResourceID):
        if rid.id is not None:
            j = self._get(f"/tokenizer/policies/access/{str(rid.id)}")
        elif rid.name is not None:
            j = self._get(f"/tokenizer/policies/access?name={rid.name}")

        return AccessPolicy.from_json(j)

    def UpdateAccessPolicy(self, access_policy: AccessPolicy):
        body = {"access_policy": access_policy.__dict__}

        j = self._put(
            f"/tokenizer/policies/access/{access_policy.id}",
            data=ucjson.dumps(body),
        )
        return AccessPolicy.from_json(j)

    def DeleteAccessPolicy(self, id: uuid.UUID, version: int):
        body = {"version": version}

        return self._delete(
            f"/tokenizer/policies/access/{str(id)}", data=ucjson.dumps(body)
        )

    ### Transformers

    def CreateTransformer(self, transformer: Transformer, if_not_exists=False):
        body = {"transformer": transformer.__dict__}

        try:
            j = self._post(
                "/tokenizer/policies/transformation", data=ucjson.dumps(body)
            )
            return Transformer.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    transformer.id = er.id
                    return transformer
            raise e

    def ListTransformers(self):
        j = self._get("/tokenizer/policies/transformation")

        policies = []
        for p in j:
            policies.append(Transformer.from_json(p))

        return policies

    # Note: Transformers are immutable, so no Update method is provided.

    def DeleteTransformer(self, id: uuid.UUID):
        return self._delete(f"/tokenizer/policies/transformation/{str(id)}")

    # Accessor Operations

    def CreateAccessor(self, accessor: Accessor, if_not_exists=False) -> Accessor:
        body = {"accessor": accessor.__dict__}

        try:
            j = self._post("/userstore/config/accessors", data=ucjson.dumps(body))
            return Accessor.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    accessor.id = er.id
                    return accessor
            raise e

    def DeleteAccessor(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/accessors/{str(id)}")

    def GetAccessor(self, id: uuid.UUID) -> Accessor:
        j = self._get(f"/userstore/config/accessors/{str(id)}")
        return Accessor.from_json(j)

    def ListAccessors(self) -> list[Accessor]:
        j = self._get("/userstore/config/accessors")
        accessors = [Accessor.from_json(a) for a in j["data"]]
        return accessors

    def UpdateAccessor(self, accessor: Accessor) -> Accessor:
        body = {"accessor": accessor.__dict__}

        j = self._put(
            f"/userstore/config/accessors/{accessor.id}",
            data=ucjson.dumps(body),
        )
        return Accessor.from_json(j)

    def ExecuteAccessor(
        self, accessor_id: uuid.UUID, context: dict, selector_values: list
    ) -> dict:
        body = {
            "accessor_id": accessor_id,
            "context": context,
            "selector_values": selector_values,
        }

        return self._post("/userstore/api/accessors", data=ucjson.dumps(body))

    # Mutator Operations
    def CreateMutator(self, mutator: Mutator, if_not_exists=False) -> Mutator:
        body = {"mutator": mutator.__dict__}

        try:
            j = self._post("/userstore/config/mutators", data=ucjson.dumps(body))
            return Mutator.from_json(j)
        except Error as e:
            if if_not_exists and e.code == 409:
                er = APIErrorResponse.from_json(e.error)
                if er.identical:
                    mutator.id = er.id
                    return mutator
            raise e

    def DeleteMutator(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/mutators/{str(id)}")

    def GetMutator(self, id: uuid.UUID) -> Mutator:
        j = self._get(f"/userstore/config/mutators/{str(id)}")
        return Mutator.from_json(j)

    def ListMutators(self) -> list[Mutator]:
        j = self._get("/userstore/config/mutators")
        mutators = [Mutator.from_json(m) for m in j["data"]]
        return mutators

    def UpdateMutator(self, mutator: Mutator) -> Mutator:
        body = {"mutator": mutator.__dict__}

        j = self._put(
            f"/userstore/config/mutators/{mutator.id}",
            data=ucjson.dumps(body),
        )
        return Mutator.from_json(j)

    def ExecuteMutator(
        self,
        mutator_id: uuid.UUID,
        context: dict,
        selector_values: list,
        row_data: dict,
    ) -> str:
        body = {
            "mutator_id": mutator_id,
            "context": context,
            "selector_values": selector_values,
            "row_data": row_data,
        }

        j = self._post("/userstore/api/mutators", data=ucjson.dumps(body))
        return j

    ### Token Operations

    def CreateToken(
        self,
        data: str,
        transformer_rid: ResourceID,
        access_policy_rid: ResourceID,
    ) -> str:
        body = {
            "data": data,
            "transformer_rid": transformer_rid.__dict__,
            "access_policy_rid": access_policy_rid.__dict__,
        }

        j = self._post("/tokenizer/tokens", data=ucjson.dumps(body))
        return j["data"]

    def ResolveTokens(
        self, tokens: list[str], context: dict, purposes: list[ResourceID]
    ) -> list[str]:
        body = {"tokens": tokens, "context": context, "purposes": purposes}

        j = self._post("/tokenizer/tokens/actions/resolve", data=ucjson.dumps(body))
        return j

    def DeleteToken(self, token: str) -> bool:
        return self._delete("/tokenizer/tokens", params={"token": token})

    def InspectToken(self, token: str) -> InspectTokenResponse:
        body = {"token": token}

        j = self._post("/tokenizer/tokens/actions/inspect", data=ucjson.dumps(body))
        return InspectTokenResponse.from_json(j)

    def LookupToken(
        self,
        data: str,
        transformer_rid: Transformer,
        access_policy_rid: AccessPolicy,
    ) -> str:
        body = {
            "data": data,
            "transformer_rid": transformer_rid.__dict__,
            "access_policy_rid": access_policy_rid.__dict__,
        }

        j = self._post("/tokenizer/tokens/actions/lookup", data=ucjson.dumps(body))
        return j["tokens"]

    # Access token helpers

    def _get_access_token(self) -> str:
        # Encode the client ID and client secret
        authorization = base64.b64encode(
            bytes(f"{self.client_id}:{self._client_secret}", "ISO-8859-1")
        ).decode("ascii")

        headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {"grant_type": "client_credentials"}

        # Note that we use requests directly here (instead of _post) because we don't
        # want to refresh the access token as we are trying to get it. :)
        r = requests.post(self.url + "/oidc/token", headers=headers, data=body)
        j = ucjson.loads(r.text)
        return j.get("access_token")

    def _refresh_access_token_if_needed(self):
        if self._access_token is None:
            return

        # TODO: this takes advantage of an implementation detail that we use JWTs for access tokens,
        # but we should probably either expose an endpoint to verify expiration time, or expect to
        # retry requests with a well-formed error, or change our bearer token format in time.
        if (
            jwt.decode(self._access_token, options={"verify_signature": False}).get(
                "exp"
            )
            < time.time()
        ):
            self._access_token = self._get_access_token()

    def _get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    # Request helpers

    def _get(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        r = requests.get(self.url + url, headers=self._get_headers(), **kwargs)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _post(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        r = requests.post(self.url + url, headers=self._get_headers(), **kwargs)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _put(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        r = requests.put(self.url + url, headers=self._get_headers(), **kwargs)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _delete(self, url, **kwargs) -> bool:
        self._refresh_access_token_if_needed()
        r = requests.delete(self.url + url, headers=self._get_headers(), **kwargs)

        if r.status_code >= 400:
            j = ucjson.loads(r.text)
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return r.status_code == 204
