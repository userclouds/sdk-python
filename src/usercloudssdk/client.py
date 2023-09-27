from __future__ import annotations

import base64
import os
import time
import urllib.parse
import uuid
from dataclasses import asdict

import jwt
import requests

from . import ucjson
from .constants import AUTHN_TYPE_PASSWORD
from .errors import UserCloudsSDKError
from .models import (
    Accessor,
    AccessPolicy,
    AccessPolicyTemplate,
    APIErrorResponse,
    Column,
    Edge,
    EdgeType,
    InspectTokenResponse,
    Mutator,
    Object,
    ObjectType,
    Organization,
    Purpose,
    ResourceID,
    Transformer,
    UserResponse,
)


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


def read_env(name: str, desc: str) -> str:
    value = os.getenv(name)
    if not value:
        raise UserCloudsSDKError(
            f"Missing environment variable '{name}': UserClouds {desc}"
        )
    return value


class Client:
    url: str
    client_id: str
    _client_secret: str
    _request_kwargs: dict
    _access_token: str

    @classmethod
    def from_env(cls, **kwargs):
        return cls(
            url=read_env("TENANT_URL", "Tenant URL"),
            id=read_env("CLIENT_ID", "Client ID"),
            secret=read_env("CLIENT_SECRET", "Client Secret"),
            **kwargs,
        )

    def __init__(self, url: str, client_id: str, client_secret: str, **kwargs):
        self.url = url
        self.client_id = urllib.parse.quote(client_id)
        self._client_secret = urllib.parse.quote(client_secret)
        self._request_kwargs = kwargs

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
            params["starting_after"] = f"id:{starting_after}"
        if email is not None:
            params["email"] = email
        params["version"] = "3"
        j = self._get("/authn/users", params=params)

        users = [UserResponse.from_json(ur) for ur in j["data"]]
        return users

    def GetUser(self, id: uuid.UUID) -> UserResponse:
        j = self._get(f"/authn/users/{id}")
        return UserResponse.from_json(j)

    def UpdateUser(self, id: uuid.UUID, profile: dict) -> UserResponse:
        body = {"profile": profile}

        j = self._put(f"/authn/users/{id}", data=ucjson.dumps(body))
        return UserResponse.from_json(j)

    def DeleteUser(self, id: uuid.UUID) -> bool:
        return self._delete(f"/authn/users/{id}")

    # Column Operations

    def CreateColumn(self, column: Column, if_not_exists=False) -> Column:
        body = {"column": column.__dict__}

        try:
            j = self._post("/userstore/config/columns", data=ucjson.dumps(body))
            return Column.from_json(j)
        except Error as e:
            if if_not_exists:
                column.id = _id_from_identical_conflict(e)
                return column
            raise e

    def DeleteColumn(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/columns/{id}")

    def GetColumn(self, id: uuid.UUID) -> Column:
        j = self._get(f"/userstore/config/columns/{id}")
        return Column.from_json(j)

    def ListColumns(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Column]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
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
            if if_not_exists:
                purpose.id = _id_from_identical_conflict(e)
                return purpose
            raise e

    def DeletePurpose(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/purposes/{id}")

    def GetPurpose(self, id: uuid.UUID) -> Purpose:
        j = self._get(f"/userstore/config/purposes/{id}")
        return Purpose.from_json(j)

    def ListPurposes(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Purpose]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/userstore/config/purposes", params=params)

        purposes = [Purpose.from_json(p) for p in j["data"]]
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
            if if_not_exists:
                access_policy_template.id = _id_from_identical_conflict(e)
                return access_policy_template
            raise e

    def ListAccessPolicyTemplates(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ):
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/tokenizer/policies/accesstemplate", params=params)

        templates = [AccessPolicyTemplate.from_json(p) for p in j["data"]]
        return templates

    def GetAccessPolicyTemplate(self, rid: ResourceID):
        if rid.id is not None:
            j = self._get(f"/tokenizer/policies/accesstemplate/{rid.id}")
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
        return self._delete(
            f"/tokenizer/policies/accesstemplate/{id}",
            params={"template_version": str(version)},
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
            if if_not_exists:
                access_policy.id = _id_from_identical_conflict(e)
                return access_policy
            raise e

    def ListAccessPolicies(self, limit: int = 0, starting_after: uuid.UUID = None):
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/tokenizer/policies/access", params=params)

        policies = [AccessPolicy.from_json(p) for p in j["data"]]
        return policies

    def GetAccessPolicy(self, rid: ResourceID):
        if rid.id is not None:
            j = self._get(f"/tokenizer/policies/access/{rid.id}")
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
        return self._delete(
            f"/tokenizer/policies/access/{id}",
            params={"policy_version": str(version)},
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
            if if_not_exists:
                transformer.id = _id_from_identical_conflict(e)
                return transformer
            raise e

    def ListTransformers(self, limit: int = 0, starting_after: uuid.UUID = None):
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/tokenizer/policies/transformation", params=params)

        transformers = [Transformer.from_json(p) for p in j["data"]]
        return transformers

    # Note: Transformers are immutable, so no Update method is provided.

    def DeleteTransformer(self, id: uuid.UUID):
        return self._delete(f"/tokenizer/policies/transformation/{id}")

    # Accessor Operations

    def CreateAccessor(self, accessor: Accessor, if_not_exists=False) -> Accessor:
        body = {"accessor": accessor.__dict__}

        try:
            j = self._post("/userstore/config/accessors", data=ucjson.dumps(body))
            return Accessor.from_json(j)
        except Error as e:
            if if_not_exists:
                accessor.id = _id_from_identical_conflict(e)
                return accessor
            raise e

    def DeleteAccessor(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/accessors/{id}")

    def GetAccessor(self, id: uuid.UUID) -> Accessor:
        j = self._get(f"/userstore/config/accessors/{id}")
        return Accessor.from_json(j)

    def ListAccessors(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Accessor]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/userstore/config/accessors", params=params)

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
    ) -> list:
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
            if if_not_exists:
                mutator.id = _id_from_identical_conflict(e)
                return mutator
            raise e

    def DeleteMutator(self, id: uuid.UUID) -> str:
        return self._delete(f"/userstore/config/mutators/{id}")

    def GetMutator(self, id: uuid.UUID) -> Mutator:
        j = self._get(f"/userstore/config/mutators/{id}")
        return Mutator.from_json(j)

    def ListMutators(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Mutator]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/userstore/config/mutators", params=params)

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

    def LookupOrCreateTokens(
        self,
        data: list[str],
        transformers: list[ResourceID],
        access_policies: list[ResourceID],
    ) -> list[str]:
        body = {
            "data": data,
            "transformer_rids": [asdict(t) for t in transformers],
            "access_policy_rids": [asdict(a) for a in access_policies],
        }

        j = self._post(
            "/tokenizer/tokens/actions/lookuporcreate", data=ucjson.dumps(body)
        )
        return j["tokens"]

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

    # AuthZ Operations

    def ListObjects(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Object]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/authz/objects", params=params)

        objects = [Object.from_json(o) for o in j["data"]]
        return objects

    def CreateObject(self, object: Object, if_not_exists=False) -> Object:
        body = object.__dict__

        try:
            j = self._post("/authz/objects", data=ucjson.dumps(body))
            return Object.from_json(j)
        except Error as e:
            if if_not_exists:
                object.id = _id_from_identical_conflict(e)
                return object
            raise e

    def GetObject(self, id: uuid.UUID) -> Object:
        j = self._get(f"/authz/objects/{id}")
        return Object.from_json(j)

    def DeleteObject(self, id: uuid.UUID):
        return self._delete(f"/authz/objects/{id}")

    def ListEdges(self, limit: int = 0, starting_after: uuid.UUID = None) -> list[Edge]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/authz/edges", params=params)

        edges = [Edge.from_json(e) for e in j["data"]]
        return edges

    def CreateEdge(self, edge: Edge, if_not_exists=False) -> Edge:
        body = edge.__dict__

        try:
            j = self._post("/authz/edges", data=ucjson.dumps(body))
            return Edge.from_json(j)
        except Error as e:
            if if_not_exists:
                edge.id = _id_from_identical_conflict(e)
                return edge
            raise e

    def GetEdge(self, id: uuid.UUID) -> Edge:
        j = self._get(f"/authz/edges/{id}")
        return Edge.from_json(j)

    def DeleteEdge(self, id: uuid.UUID):
        return self._delete(f"/authz/edges/{id}")

    def ListObjectTypes(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[ObjectType]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/authz/objecttypes", params=params)

        object_types = [ObjectType.from_json(ot) for ot in j["data"]]
        return object_types

    def CreateObjectType(
        self, object_type: ObjectType, if_not_exists=False
    ) -> ObjectType:
        body = object_type.__dict__

        try:
            j = self._post("/authz/objecttypes", data=ucjson.dumps(body))
            return ObjectType.from_json(j)
        except Error as e:
            if if_not_exists:
                object_type.id = _id_from_identical_conflict(e)
                return object_type
            raise e

    def GetObjectType(self, id: uuid.UUID) -> ObjectType:
        j = self._get(f"/authz/objecttypes/{id}")
        return ObjectType.from_json(j)

    def DeleteObjectType(self, id: uuid.UUID):
        return self._delete(f"/authz/objecttypes/{id}")

    def ListEdgeTypes(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[EdgeType]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/authz/edgetypes", params=params)

        edge_types = [EdgeType.from_json(et) for et in j["data"]]
        return edge_types

    def CreateEdgeType(self, edge_type: EdgeType, if_not_exists=False) -> EdgeType:
        body = edge_type.__dict__

        try:
            j = self._post("/authz/edgetypes", data=ucjson.dumps(body))
            return EdgeType.from_json(j)
        except Error as e:
            if if_not_exists:
                edge_type.id = _id_from_identical_conflict(e)
                return edge_type
            raise e

    def GetEdgeType(self, id: uuid.UUID) -> EdgeType:
        j = self._get(f"/authz/edgetypes/{id}")
        return EdgeType.from_json(j)

    def DeleteEdgeType(self, id: uuid.UUID):
        return self._delete(f"/authz/edgetypes/{id}")

    def ListOrganizations(
        self, limit: int = 0, starting_after: uuid.UUID = None
    ) -> list[Organization]:
        params = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        j = self._get("/authz/organizations", params=params)

        organizations = [Organization.from_json(o) for o in j["data"]]
        return organizations

    def CreateOrganization(self, organization: Organization) -> Organization:
        body = organization.__dict__
        j = self._post("/authz/organizations", data=ucjson.dumps(body))
        return Organization.from_json(j)

    def GetOrganization(self, id: uuid.UUID) -> Organization:
        j = self._get(f"/authz/organizations/{id}")
        return Organization.from_json(j)

    def DeleteOrganization(self, id: uuid.UUID):
        return self._delete(f"/authz/organizations/{id}")

    def CheckAttribute(
        self,
        source_object_id: uuid.UUID,
        target_object_id: uuid.UUID,
        attribute_name: str,
    ) -> bool:
        j = self._get(
            f"/authz/checkattribute?source_object_id={source_object_id}&target_object_id={target_object_id}&attribute={attribute_name}"
        )
        return j.get("has_attribute")

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
        r = requests.post(
            self.url + "/oidc/token",
            headers=headers,
            data=body,
            **self._request_kwargs,
        )
        j = ucjson.loads(r.text)
        return j.get("access_token")

    def _refresh_access_token_if_needed(self):
        if self._access_token is None:
            return

        # TODO: this takes advantage of an implementation detail that we use JWTs for
        # access tokens, but we should probably either expose an endpoint to verify
        # expiration time, or expect to retry requests with a well-formed error, or
        # change our bearer token format in time.
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
        args = self._request_kwargs.copy()
        args.update(kwargs)
        r = requests.get(self.url + url, headers=self._get_headers(), **args)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _post(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        r = requests.post(self.url + url, headers=self._get_headers(), **args)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _put(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        r = requests.put(self.url + url, headers=self._get_headers(), **args)
        j = ucjson.loads(r.text)

        if r.status_code >= 400:
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return j

    def _delete(self, url, **kwargs) -> bool:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        r = requests.delete(self.url + url, headers=self._get_headers(), **args)

        if r.status_code >= 400:
            j = ucjson.loads(r.text)
            e = Error.from_json(j)
            e.code = r.status_code
            raise e

        return r.status_code == 204


def _id_from_identical_conflict(e):
    if e.code == 409:
        er = APIErrorResponse.from_json(e.error)
        if er.identical:
            return er.id
    raise e
