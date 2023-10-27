from __future__ import annotations

import base64
import os
import time
import urllib.parse
import uuid
from dataclasses import asdict

import httpx
import jwt

from . import ucjson
from .constants import AUTHN_TYPE_PASSWORD
from .errors import UserCloudsSDKError
from .models import (
    Accessor,
    AccessPolicy,
    AccessPolicyTemplate,
    APIErrorResponse,
    Column,
    ColumnRetentionDurationResponse,
    ColumnRetentionDurationsResponse,
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
    UpdateColumnRetentionDurationRequest,
    UpdateColumnRetentionDurationsRequest,
    UserResponse,
)


class Error(Exception):
    def __init__(
        self,
        error: str | dict = "unspecified error",
        http_status_code: int = -1,
        request_id: str | None = None,
    ) -> None:
        super().__init__(error)
        self._err = error
        self.error_json = error if isinstance(error, dict) else None
        self.code = http_status_code
        self.request_id = request_id

    def __repr__(self):
        return f"Error({self._err}, {self.code}, {self.request_id})"

    @classmethod
    def from_response(cls, resp) -> Error:
        request_id = resp.headers.get("X-Request-Id")
        if _is_json(resp):
            resp_json = ucjson.loads(resp.text)
            return cls(
                error=resp_json["error"],
                request_id=resp_json.get("request_id", request_id),
                http_status_code=resp.status_code,
            )
        else:
            return cls(
                error=f"HTTP {resp.status_code} - {resp.text}",
                request_id=request_id,
                http_status_code=resp.status_code,
            )


def read_env(name: str, desc: str) -> str:
    value = os.getenv(name)
    if not value:
        raise UserCloudsSDKError(
            f"Missing environment variable '{name}': UserClouds {desc}"
        )
    return value


def create_http_client(url: str):
    return httpx.Client(base_url=url)


def _is_json(resp) -> bool:
    return resp.headers.get("Content-Type") == "application/json"


class Client:
    @classmethod
    def from_env(cls, client_factory=create_http_client, **kwargs):
        return cls(
            url=read_env("TENANT_URL", "Tenant URL"),
            client_id=read_env("CLIENT_ID", "Client ID"),
            client_secret=read_env("CLIENT_SECRET", "Client Secret"),
            client_factory=client_factory,
            **kwargs,
        )

    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        client_factory=create_http_client,
        **kwargs,
    ):
        self._authorization = base64.b64encode(
            bytes(
                f"{ urllib.parse.quote(client_id)}:{ urllib.parse.quote(client_secret)}",
                "ISO-8859-1",
            )
        ).decode("ascii")
        self._client = client_factory(url)
        self._request_kwargs = kwargs
        self._access_token: str | None = None  # lazy loaded

    # User Operations

    def CreateUser(self) -> uuid.UUID:
        resp_json = self._post("/authn/users", data=ucjson.dumps({}))
        return resp_json.get("id")

    def CreateUserWithPassword(self, username: str, password: str) -> uuid.UUID:
        body = {
            "username": username,
            "password": password,
            "authn_type": AUTHN_TYPE_PASSWORD,
        }

        resp_json = self._post("/authn/users", data=ucjson.dumps(body))
        return resp_json.get("id")

    def ListUsers(
        self,
        limit: int = 0,
        starting_after: uuid.UUID | None = None,
        email: str | None = None,
    ) -> list[UserResponse]:
        params: dict[str, str | int] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        if email is not None:
            params["email"] = email
        params["version"] = "3"
        resp_json = self._get("/authn/users", params=params)

        users = [UserResponse.from_json(ur) for ur in resp_json["data"]]
        return users

    def GetUser(self, id: uuid.UUID) -> UserResponse:
        resp_json = self._get(f"/authn/users/{id}")
        return UserResponse.from_json(resp_json)

    def UpdateUser(self, id: uuid.UUID, profile: dict) -> UserResponse:
        body = {"profile": profile}
        resp_json = self._put(f"/authn/users/{id}", data=ucjson.dumps(body))
        return UserResponse.from_json(resp_json)

    def DeleteUser(self, id: uuid.UUID) -> bool:
        return self._delete(f"/authn/users/{id}")

    # Column Operations

    def CreateColumn(self, column: Column, if_not_exists=False) -> Column:
        body = {"column": column.__dict__}
        try:
            resp_json = self._post("/userstore/config/columns", data=ucjson.dumps(body))
            return Column.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                column.id = _id_from_identical_conflict(err)
                return column
            raise err

    def DeleteColumn(self, id: uuid.UUID) -> bool:
        return self._delete(f"/userstore/config/columns/{id}")

    def GetColumn(self, id: uuid.UUID) -> Column:
        resp_json = self._get(f"/userstore/config/columns/{id}")
        return Column.from_json(resp_json)

    def ListColumns(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Column]:
        params: dict[str, int | str] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/userstore/config/columns", params=params)
        columns = [Column.from_json(col) for col in resp_json["data"]]
        return columns

    def UpdateColumn(self, column: Column) -> Column:
        body = {"column": column.__dict__}

        resp_json = self._put(
            f"/userstore/config/columns/{column.id}", data=ucjson.dumps(body)
        )
        return Column.from_json(resp_json)

    # Purpose Operations

    def CreatePurpose(self, purpose: Purpose, if_not_exists=False) -> Purpose:
        body = {"purpose": purpose.__dict__}

        try:
            resp_json = self._post(
                "/userstore/config/purposes", data=ucjson.dumps(body)
            )
            return Purpose.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                purpose.id = _id_from_identical_conflict(err)
                return purpose
            raise err

    def DeletePurpose(self, id: uuid.UUID) -> bool:
        return self._delete(f"/userstore/config/purposes/{id}")

    def GetPurpose(self, id: uuid.UUID) -> Purpose:
        json_resp = self._get(f"/userstore/config/purposes/{id}")
        return Purpose.from_json(json_resp)

    def ListPurposes(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Purpose]:
        params: dict[str, str | int] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/userstore/config/purposes", params=params)
        purposes = [Purpose.from_json(p) for p in resp_json["data"]]
        return purposes

    def UpdatePurpose(self, purpose: Purpose) -> Purpose:
        body = {"purpose": purpose.__dict__}

        resp_json = self._put(
            f"/userstore/config/purposes/{purpose.id}", data=ucjson.dumps(body)
        )
        return Purpose.from_json(resp_json)

    # Retention Duration Operations

    # Tenant Retention Duration

    # A configured tenant retention duration will apply for
    # all column purposes that do not have a configured purpose
    # retention duration default or a configured column purpose
    # retention duration. If a tenant retention duration is
    # not configured, soft-deleted values will not be retained
    # by default.

    # create a tenant retention duration default
    def CreateSoftDeletedRetentionDurationOnTenant(
        self, req: UpdateColumnRetentionDurationRequest
    ) -> ColumnRetentionDurationResponse:
        resp = self._post(
            "/userstore/config/softdeletedretentiondurations", data=req.to_json()
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # delete a tenant retention duration default
    def DeleteSoftDeletedRetentionDurationOnTenant(self, durationID: uuid.UUID) -> bool:
        return self._delete(
            f"/userstore/config/softdeletedretentiondurations/{durationID}"
        )

    # get a specific tenant retention duration default
    def GetSoftDeletedRetentionDurationOnTenant(
        self, durationID: uuid.UUID
    ) -> ColumnRetentionDurationResponse:
        resp = self._get(
            f"/userstore/config/softdeletedretentiondurations/{durationID}"
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # get tenant retention duration, or default value if not specified
    def GetDefaultSoftDeletedRetentionDurationOnTenant(
        self,
    ) -> ColumnRetentionDurationResponse:
        resp = self._get("/userstore/config/softdeletedretentiondurations")
        return ColumnRetentionDurationResponse.from_json(resp)

    # update a specific tenant retention duration default
    def UpdateSoftDeletedRetentionDurationOnTenant(
        self, durationID: uuid.UUID, req: UpdateColumnRetentionDurationRequest
    ) -> ColumnRetentionDurationResponse:
        resp = self._put(
            f"/userstore/config/softdeletedretentiondurations/{durationID}",
            req.to_json(),
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # Purpose Retention Durations

    # A configured purpose retention duration will apply for all
    # column purposes that include the specified purpose, unless
    # a retention duration has been configured for a specific
    # column purpose.

    # create a purpose retention duration default
    def CreateSoftDeletedRetentionDurationOnPurpose(
        self, purposeID: uuid.UUID, req: UpdateColumnRetentionDurationRequest
    ) -> ColumnRetentionDurationResponse:
        resp = self._post(
            f"/userstore/config/purposes/{purposeID}/softdeletedretentiondurations",
            data=req.to_json(),
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # delete a purpose retention duration default
    def DeleteSoftDeletedRetentionDurationOnPurpose(
        self, purposeID: uuid.UUID, durationID: uuid.UUID
    ) -> bool:
        return self._delete(
            f"/userstore/config/purposes/{purposeID}/softdeletedretentiondurations/{durationID}"
        )

    # get a specific purpose retention duration default
    def GetSoftDeletedRetentionDurationOnPurpose(
        self, purposeID: uuid.UUID, durationID: uuid.UUID
    ) -> ColumnRetentionDurationResponse:
        resp = self._get(
            f"/userstore/config/purposes/{purposeID}/softdeletedretentiondurations/{durationID}"
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # get purpose retention duration, or default value if not specified
    def GetDefaultSoftDeletedRetentionDurationOnPurpose(
        self, purposeID: uuid.UUID
    ) -> ColumnRetentionDurationResponse:
        resp = self._get(
            f"/userstore/config/purposes/{purposeID}/softdeletedretentiondurations"
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # update a specific purpose retention duration default
    def UpdateSoftDeletedRetentionDurationOnPurpose(
        self,
        purposeID: uuid.UUID,
        durationID: uuid.UUID,
        req: UpdateColumnRetentionDurationRequest,
    ) -> ColumnRetentionDurationResponse:
        resp = self._put(
            f"/userstore/config/purposes/{purposeID}/softdeletedretentiondurations/{durationID}",
            req.to_json(),
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # Column Retention Durations

    # A configured column purpose retention duration will override
    # any configured purpose level, tenant level, or system-level
    # default retention durations.

    # get a specific column purpose retention duration
    def GetSoftDeletedRetentionDurationOnColumn(
        self, columnID: uuid.UUID, durationID: uuid.UUID
    ) -> ColumnRetentionDurationResponse:
        resp = self._get(
            f"/userstore/config/columns/{columnID}/softdeletedretentiondurations/{durationID}"
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # get the retention duration for each purpose for a given column
    def GetSoftDeletedRetentionDurationsOnColumn(
        self, columnID: uuid.UUID
    ) -> ColumnRetentionDurationsResponse:
        resp = self._get(
            f"/userstore/config/columns/{columnID}/softdeletedretentiondurations"
        )
        return ColumnRetentionDurationsResponse.from_json(resp)

    # delete a specific column purpose retention duration
    def DeleteSoftDeletedRetentionDurationOnColumn(
        self, columnID: uuid.UUID, durationID: uuid.UUID
    ) -> bool:
        return self._delete(
            f"/userstore/config/columns/{columnID}/softdeletedretentiondurations/{durationID}"
        )

    # update a specific column purpose retention duration
    def UpdateSoftDeletedRetentionDurationOnColumn(
        self,
        columnID: uuid.UUID,
        durationID: uuid.UUID,
        req: UpdateColumnRetentionDurationRequest,
    ) -> ColumnRetentionDurationResponse:
        resp = self._put(
            f"/userstore/config/columns/{columnID}/softdeletedretentiondurations/{durationID}",
            req.to_json(),
        )
        return ColumnRetentionDurationResponse.from_json(resp)

    # update the specified purpose retention durations for the column
    # - durations can be added, deleted, or updated for each purpose
    def UpdateSoftDeletedRetentionDurationsOnColumn(
        self, columnID: uuid.UUID, req: UpdateColumnRetentionDurationsRequest
    ) -> ColumnRetentionDurationsResponse:
        resp = self._post(
            f"/userstore/config/columns/{columnID}/softdeletedretentiondurations",
            data=req.to_json(),
        )
        return ColumnRetentionDurationsResponse.from_json(resp)

    # Access Policy Templates

    def CreateAccessPolicyTemplate(
        self, access_policy_template: AccessPolicyTemplate, if_not_exists=False
    ) -> AccessPolicyTemplate | Error:
        body = {"access_policy_template": access_policy_template.__dict__}

        try:
            resp_json = self._post(
                "/tokenizer/policies/accesstemplate", data=ucjson.dumps(body)
            )
            return AccessPolicyTemplate.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                access_policy_template.id = _id_from_identical_conflict(err)
                return access_policy_template
            raise err

    def ListAccessPolicyTemplates(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ):
        params: dict[str, int | str] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/tokenizer/policies/accesstemplate", params=params)

        templates = [AccessPolicyTemplate.from_json(apt) for apt in resp_json["data"]]
        return templates

    def GetAccessPolicyTemplate(self, rid: ResourceID):
        if rid.id is not None:
            resp_json = self._get(f"/tokenizer/policies/accesstemplate/{rid.id}")
        elif rid.name is not None:
            resp_json = self._get(f"/tokenizer/policies/accesstemplate?name={rid.name}")

        return AccessPolicyTemplate.from_json(resp_json)

    def UpdateAccessPolicyTemplate(self, access_policy_template: AccessPolicyTemplate):
        body = {"access_policy_template": access_policy_template.__dict__}

        resp_json = self._put(
            f"/tokenizer/policies/accesstemplate/{access_policy_template.id}",
            data=ucjson.dumps(body),
        )
        return AccessPolicyTemplate.from_json(resp_json)

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
            resp_json = self._post(
                "/tokenizer/policies/access", data=ucjson.dumps(body)
            )
            return AccessPolicy.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                access_policy.id = _id_from_identical_conflict(err)
                return access_policy
            raise err

    def ListAccessPolicies(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ):
        params: dict[str, str | int] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/tokenizer/policies/access", params=params)

        policies = [AccessPolicy.from_json(ap) for ap in resp_json["data"]]
        return policies

    def GetAccessPolicy(self, rid: ResourceID):
        if rid.id is not None:
            resp_json = self._get(f"/tokenizer/policies/access/{rid.id}")
        elif rid.name is not None:
            resp_json = self._get(f"/tokenizer/policies/access?name={rid.name}")

        return AccessPolicy.from_json(resp_json)

    def UpdateAccessPolicy(self, access_policy: AccessPolicy):
        body = {"access_policy": access_policy.__dict__}

        resp_json = self._put(
            f"/tokenizer/policies/access/{access_policy.id}",
            data=ucjson.dumps(body),
        )
        return AccessPolicy.from_json(resp_json)

    def DeleteAccessPolicy(self, id: uuid.UUID, version: int):
        return self._delete(
            f"/tokenizer/policies/access/{id}",
            params={"policy_version": str(version)},
        )

    # Transformers

    def CreateTransformer(self, transformer: Transformer, if_not_exists=False):
        body = {"transformer": transformer.__dict__}

        try:
            resp_json = self._post(
                "/tokenizer/policies/transformation", data=ucjson.dumps(body)
            )
            return Transformer.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                transformer.id = _id_from_identical_conflict(err)
                return transformer
            raise err

    def ListTransformers(self, limit: int = 0, starting_after: uuid.UUID | None = None):
        params: dict[str, str | int] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/tokenizer/policies/transformation", params=params)
        transformers = [Transformer.from_json(tf) for tf in resp_json["data"]]
        return transformers

    # Note: Transformers are immutable, so no Update method is provided.

    def DeleteTransformer(self, id: uuid.UUID):
        return self._delete(f"/tokenizer/policies/transformation/{id}")

    # Accessor Operations

    def CreateAccessor(self, accessor: Accessor, if_not_exists=False) -> Accessor:
        body = {"accessor": accessor.__dict__}

        try:
            resp_json = self._post(
                "/userstore/config/accessors", data=ucjson.dumps(body)
            )
            return Accessor.from_json(resp_json)
        except Error as err:
            if if_not_exists:
                accessor.id = _id_from_identical_conflict(err)
                return accessor
            raise err

    def DeleteAccessor(self, id: uuid.UUID) -> bool:
        return self._delete(f"/userstore/config/accessors/{id}")

    def GetAccessor(self, id: uuid.UUID) -> Accessor:
        j = self._get(f"/userstore/config/accessors/{id}")
        return Accessor.from_json(j)

    def ListAccessors(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Accessor]:
        params: dict[str, str | int] = {}
        if limit > 0:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = f"id:{starting_after}"
        params["version"] = "3"
        resp_json = self._get("/userstore/config/accessors", params=params)

        accessors = [Accessor.from_json(acs) for acs in resp_json["data"]]
        return accessors

    def UpdateAccessor(self, accessor: Accessor) -> Accessor:
        body = {"accessor": accessor.__dict__}

        resp_json = self._put(
            f"/userstore/config/accessors/{accessor.id}",
            data=ucjson.dumps(body),
        )
        return Accessor.from_json(resp_json)

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

    def DeleteMutator(self, id: uuid.UUID) -> bool:
        return self._delete(f"/userstore/config/mutators/{id}")

    def GetMutator(self, id: uuid.UUID) -> Mutator:
        j = self._get(f"/userstore/config/mutators/{id}")
        return Mutator.from_json(j)

    def ListMutators(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Mutator]:
        params: dict[str, str | int] = {}
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

    # Token Operations

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

        json_resp = self._post("/tokenizer/tokens", data=ucjson.dumps(body))
        return json_resp["data"]

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
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Object]:
        params: dict[str, str | int] = {}
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

    def ListEdges(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Edge]:
        params: dict[str, str | int] = {}
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
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[ObjectType]:
        params: dict[str, str | int] = {}
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
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[EdgeType]:
        params: dict[str, str | int] = {}
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

    def DeleteEdgeType(self, id: uuid.UUID) -> bool:
        return self._delete(f"/authz/edgetypes/{id}")

    def ListOrganizations(
        self, limit: int = 0, starting_after: uuid.UUID | None = None
    ) -> list[Organization]:
        params: dict[str, str | int] = {}
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
        json_data = self._post("/authz/organizations", data=ucjson.dumps(body))
        return Organization.from_json(json_data)

    def GetOrganization(self, id: uuid.UUID) -> Organization:
        json_data = self._get(f"/authz/organizations/{id}")
        return Organization.from_json(json_data)

    def DeleteOrganization(self, id: uuid.UUID) -> bool:
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

    def DownloadUserstoreSDK(self) -> str:
        return self._download("/userstore/download/codegensdk.py")

    # Access Token Helpers

    def _get_access_token(self) -> str:
        # Encode the client ID and client secret
        headers = {
            "Authorization": f"Basic {self._authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {"grant_type": "client_credentials"}

        # Note that we use requests directly here (instead of _post) because we don't
        # want to refresh the access token as we are trying to get it. :)
        resp = self._client.post(
            "/oidc/token",
            headers=headers,
            data=body,
            **self._request_kwargs,
        )
        if resp.status_code >= 400:
            raise Error.from_response(resp)
        json_data = ucjson.loads(resp.text)
        return json_data.get("access_token")

    def _refresh_access_token_if_needed(self) -> None:
        if self._access_token is None:
            self._access_token = self._get_access_token()
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

    # Request Helpers

    def _get(self, url, **kwargs) -> dict:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        resp = self._client.get(url, headers=self._get_headers(), **args)
        if resp.status_code >= 400:
            raise Error.from_response(resp)
        return ucjson.loads(resp.text)

    def _post(self, url, **kwargs) -> dict | list:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        resp = self._client.post(url, headers=self._get_headers(), **args)
        if resp.status_code >= 400:
            raise Error.from_response(resp)
        return ucjson.loads(resp.text)

    def _put(self, url, **kwargs) -> dict | list:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        resp = self._client.put(url, headers=self._get_headers(), **args)
        if resp.status_code >= 400:
            raise Error.from_response(resp)
        return ucjson.loads(resp.text)

    def _delete(self, url, **kwargs) -> bool:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        resp = self._client.delete(url, headers=self._get_headers(), **args)

        if resp.status_code == 404:
            return False

        if resp.status_code >= 400:
            raise Error.from_response(resp)
        return resp.status_code == 204

    def _download(self, url, **kwargs) -> str:
        self._refresh_access_token_if_needed()
        args = self._request_kwargs.copy()
        args.update(kwargs)
        resp = self._client.get(url, headers=self._get_headers(), **args)
        return resp.text


def _id_from_identical_conflict(err: Error) -> uuid.UUID:
    if err.code == 409:
        api_error = APIErrorResponse.from_json(err.error_json)
        if api_error.identical:
            return api_error.id
    raise err
