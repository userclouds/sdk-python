from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

import iso8601

from . import ucjson


class User:
    id: uuid.UUID
    profile: dict

    def __init__(self, id: uuid.UUID, profile: dict) -> None:
        self.id = id
        self.profile = profile

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "profile": self.profile,
            }
        )

    @classmethod
    def from_json(cls, json_data) -> User:
        return cls(
            id=uuid.UUID(json_data["id"]),
            profile=json_data["profile"],
        )


class UserResponse:
    id: uuid.UUID
    updated_at: datetime.datetime
    profile: dict
    organization_id: uuid.UUID

    def __init__(
        self,
        id: uuid.UUID,
        updated_at: datetime.datetime,
        profile: dict,
        organization_id: uuid.UUID,
    ) -> None:
        self.id = id
        self.updated_at = updated_at
        self.profile = profile
        self.organization_id = organization_id

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "updated_at": self.updated_at.isoformat(),
                "profile": self.profile,
                "organization_id": str(self.organization_id),
            }
        )

    @classmethod
    def from_json(cls, json_data: dict) -> UserResponse:
        return cls(
            id=uuid.UUID(json_data["id"]),
            updated_at=datetime.datetime.fromtimestamp(json_data["updated_at"]),
            profile=json_data["profile"],
            organization_id=uuid.UUID(json_data["organization_id"]),
        )


class UserSelectorConfig:
    where_clause: str

    def __init__(self, where_clause: str) -> None:
        self.where_clause = where_clause

    def to_json(self) -> str:
        return ucjson.dumps({"where_clause": self.where_clause})

    @classmethod
    def from_json(cls, json_data) -> UserSelectorConfig:
        return cls(where_clause=json_data["where_clause"])


class ResourceID:
    def __init__(self, id="", name="") -> None:
        if id != "":
            setattr(self, "id", id)
        if name != "":
            setattr(self, "name", name)

    def __repr__(self) -> str:
        if hasattr(self, "id"):
            return f"ResourceID({self.id})"
        elif hasattr(self, "name"):
            return f"ResourceID({self.name})"
        else:
            return "ResourceID()"

    def isValid(self) -> bool:
        return hasattr(self, "id") or hasattr(self, "name")

    @classmethod
    def from_json(cls, json_data) -> ResourceID:
        return cls(id=json_data["id"], name=json_data["name"])


class Column:
    id: uuid.UUID
    name: str
    type: str
    is_array: bool
    default_value: str
    index_type: str

    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        type: str,
        is_array: bool,
        default_value: str,
        index_type: str,
    ) -> None:
        self.id = id
        self.name = name
        self.type = type
        self.is_array = is_array
        self.default_value = default_value
        self.index_type = index_type

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "type": self.type,
                "is_array": self.is_array,
                "default_value": self.default_value,
                "index_type": self.index_type,
            }
        )

    @classmethod
    def from_json(cls, json_data) -> Column:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            type=json_data["type"],
            is_array=json_data["is_array"],
            default_value=json_data["default_value"],
            index_type=json_data["index_type"],
        )


class Purpose:
    id: uuid.UUID
    name: str
    description: str

    def __init__(self, id: uuid.UUID, name: str, description: str) -> None:
        self.id = id
        self.name = name
        self.description = description

    def to_json(self) -> str:
        return ucjson.dumps(
            {"id": str(self.id), "name": self.name, "description": self.description}
        )

    @classmethod
    def from_json(cls, json_data: dict) -> Purpose:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            description=json_data["description"],
        )


class ColumnOutputConfig:
    column: ResourceID
    transformer: ResourceID

    def __init__(self, column: ResourceID, transformer: ResourceID) -> None:
        self.column = column
        self.transformer = transformer

    @classmethod
    def from_json(cls, json_data: dict) -> ColumnOutputConfig:
        return ColumnOutputConfig(
            column=ResourceID.from_json(json_data["column"]),
            transformer=ResourceID.from_json(json_data["transformer"]),
        )


class Accessor:
    id: uuid.UUID
    name: str
    description: str
    columns: list[ColumnOutputConfig]
    access_policy: ResourceID
    token_access_policy: ResourceID | None
    selector_config: UserSelectorConfig
    purposes: list[ResourceID]
    version: int

    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        description: str,
        columns: list[ColumnOutputConfig],
        access_policy: ResourceID,
        selector_config: UserSelectorConfig,
        purposes: list[ResourceID],
        token_access_policy: ResourceID | None = None,
        version: int = 0,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.columns = columns
        self.access_policy = access_policy
        self.selector_config = selector_config
        self.purposes = purposes
        self.token_access_policy = token_access_policy
        self.version = version

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "columns": self.columns,
                "access_policy": self.access_policy,
                "selector_config": self.selector_config.to_json(),
                "purposes": self.purposes,
                "token_access_policy": self.token_access_policy,
            }
        )

    @classmethod
    def from_json(cls, json_data: dict) -> Accessor:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            description=json_data["description"],
            columns=json_data["columns"],
            access_policy=ResourceID.from_json(json_data["access_policy"]),
            selector_config=UserSelectorConfig.from_json(json_data["selector_config"]),
            purposes=json_data["purposes"],
            token_access_policy=ResourceID.from_json(json_data["token_access_policy"]),
            version=json_data["version"],
        )

    def __str__(self) -> str:
        return f"Accessor - {self.name} - {self.id}"


class ColumnInputConfig:
    column: ResourceID
    validator: ResourceID

    def __init__(self, column: ResourceID, validator: ResourceID) -> None:
        self.column = column
        self.validator = validator

    @classmethod
    def from_json(cls, json_data: dict) -> ColumnInputConfig:
        return cls(
            column=ResourceID.from_json(json_data["column"]),
            validator=ResourceID.from_json(json_data["validator"]),
        )


class Mutator:
    id: uuid.UUID
    name: str
    description: str
    columns: list[ColumnInputConfig]
    access_policy: ResourceID
    selector_config: UserSelectorConfig
    version: int

    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        description: str,
        columns: list[ColumnInputConfig],
        access_policy: ResourceID,
        selector_config: UserSelectorConfig,
        version: int = 0,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.columns = columns
        self.access_policy = access_policy
        self.selector_config = selector_config
        self.version = version

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "columns": self.columns,
                "access_policy": str(self.access_policy),
                "selector_config": self.selector_config.to_json(),
            }
        )

    @classmethod
    def from_json(cls, json_data: dict) -> Mutator:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            description=json_data["description"],
            columns=json_data["columns"],
            access_policy=ResourceID.from_json(json_data["access_policy"]),
            selector_config=UserSelectorConfig.from_json(json_data["selector_config"]),
            version=json_data["version"],
        )

    def __str__(self) -> str:
        return f"mutator {self.name} - {self.id}"


class AccessPolicyTemplate:
    id: uuid.UUID
    name: str
    description: str
    function: str
    version: int

    def __init__(
        self,
        id=uuid.UUID(int=0),
        name="",
        description="",
        function="",
        version=0,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.function = function
        self.version = version

    def __repr__(self) -> str:
        return f"AccessPolicyTemplate({self.id})"

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "description": self.description,
                "function": self.function,
                "version": self.version,
            }
        )

    @classmethod
    def from_json(cls, json_data: dict) -> AccessPolicyTemplate:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            description=json_data["description"],
            function=json_data["function"],
            version=json_data["version"],
        )


class AccessPolicyComponent:
    def __init__(self, policy="", template="", template_parameters="") -> None:
        if policy != "":
            setattr(self, "policy", policy)
        if template != "":
            setattr(self, "template", template)
            setattr(self, "template_parameters", template_parameters)

    def __repr__(self) -> str:
        if hasattr(self, "policy"):
            return f"AccessPolicyComponent({self.policy})"
        elif hasattr(self, "template"):
            return f"AccessPolicyComponent({self.template})"
        else:
            return "AccessPolicyComponent()"

    def to_json(self) -> str:
        obj = {}
        if self.policy:
            obj["policy"] = self.policy.to_json()
        if self.template:
            obj["template"] = self.template.to_json()
            obj["template_parameters"] = self.template_parameters
        return ucjson.dumps(obj)

    @classmethod
    def from_json(cls, json_data: dict) -> AccessPolicyComponent:
        return cls(
            policy=json_data["policy"] if "policy" in json_data else "",
            template=json_data["template"] if "template" in json_data else "",
            template_parameters=json_data["template_parameters"]
            if "template_parameters" in json_data
            else "",
        )


class AccessPolicy:
    id: uuid.UUID
    name: str
    description: str
    policy_type: str
    version: int
    components: list[AccessPolicyComponent]

    def __init__(
        self,
        id=uuid.UUID(int=0),
        name="",
        description="",
        policy_type="",
        version=0,
        components=[],
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.policy_type = policy_type
        self.version = version
        self.components = components

    def __repr__(self) -> str:
        return f"AccessPolicy({self.id})"

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "description": self.description,
                "policy_type": self.policy_type,
                "version": self.version,
                "components": [c.to_json() for c in self.components],
            }
        )

    @classmethod
    def from_json(cls, json_data: dict) -> AccessPolicy:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            description=json_data["description"],
            policy_type=json_data["policy_type"],
            version=json_data["version"],
            components=[
                AccessPolicyComponent.from_json(apc) for apc in json_data["components"]
            ],
        )


class Transformer:
    id: uuid.UUID
    name: str
    input_type: str
    output_type: str
    reuse_existing_token: bool
    transform_type: str
    function: str
    parameters: str

    def __init__(
        self,
        id=uuid.UUID(int=0),
        name="",
        input_type="",
        output_type="",
        reuse_existing_token=False,
        transform_type="",
        function="",
        parameters="",
    ) -> None:
        self.id = id
        self.name = name
        self.input_type = input_type
        self.output_type = output_type
        self.reuse_existing_token = reuse_existing_token
        self.transform_type = transform_type
        self.function = function
        self.parameters = parameters

    def __repr__(self) -> str:
        return f"Transformer({self.id})"

    def __str__(self) -> str:
        return f"transformer {self.name} - {self.id}"

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "input_type": self.input_type,
                "output_type": self.output_type,
                "reuse_existing_token": self.reuse_existing_token,
                "transform_type": self.transform_type,
                "function": self.function,
                "parameters": self.parameters,
            },
        )

    @classmethod
    def from_json(cls, json_data: dict) -> Transformer:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            input_type=json_data["input_type"],
            output_type=json_data["output_type"],
            reuse_existing_token=json_data["reuse_existing_token"],
            transform_type=json_data["transform_type"],
            function=json_data["function"],
            parameters=json_data["parameters"],
        )


class RetentionDuration:
    unit: str
    duration: int

    def __init__(self, unit: str, duration: int):
        self.unit = unit
        self.duration = duration

    def __repr__(self) -> str:
        return f"RetentionDuration(unit: '{self.unit}', duration: '{self.duration}')"

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "unit": self.unit,
                "duration": self.duration,
            }
        )

    @classmethod
    def from_json(cls, data: dict) -> RetentionDuration:
        return cls(
            unit=data["unit"],
            duration=data["duration"],
        )


class ColumnRetentionDuration:
    duration_type: str
    id: uuid.UUID
    column_id: uuid.UUID
    purpose_id: uuid.UUID
    duration: RetentionDuration
    use_default: bool
    default_duration: RetentionDuration
    purpose_name: str
    version: int

    def __init__(
        self,
        duration_type,
        duration,
        id=uuid.UUID(int=0),
        column_id=uuid.UUID(int=0),
        purpose_id=uuid.UUID(int=0),
        use_default=False,
        default_duration=None,
        purpose_name=None,
        version=0,
    ):
        self.duration_type = duration_type
        self.id = id
        self.column_id = column_id
        self.purpose_id = purpose_id
        self.duration = duration
        self.use_default = use_default
        self.default_duration = default_duration
        self.purpose_name = purpose_name
        self.version = version

    def __repr__(self):
        return f"ColumnRetentionDuration(duration_type: '{self.duration_type}', duration: '{self.duration}', id: '{self.id}', column_id: '{self.column_id}', purpose_id: '{self.purpose_id}', use_default: '{self.use_default}', default_duration: '{self.default_duration}', purpose_name: '{self.purpose_name}', version: '{self.version}')"

    def to_json(self):
        default_duration = (
            None if self.default_duration is None else self.default_duration.to_json()
        )
        return ucjson.dumps(
            {
                "duration_type": self.duration_type,
                "id": str(self.id),
                "column_id": str(self.column_id),
                "purpose_id": str(self.purpose_id),
                "duration": self.duration.to_json(),
                "use_default": self.use_default,
                "default_duration": default_duration,
                "purpose_name": self.purpose_name,
                "version": self.version,
            }
        )

    @classmethod
    def from_json(cls, data):
        return cls(
            data["duration_type"],
            RetentionDuration.from_json(data["duration"]),
            uuid.UUID(data["id"]),
            uuid.UUID(data["column_id"]),
            uuid.UUID(data["purpose_id"]),
            data["use_default"],
            RetentionDuration.from_json(data["default_duration"]),
            data["purpose_name"],
            data["version"],
        )


class UpdateColumnRetentionDurationRequest:
    retention_duration: ColumnRetentionDuration

    def __init__(
        self,
        retention_duration,
    ):
        self.retention_duration = retention_duration

    def __repr__(self):
        return f"UpdateColumnRetentionDurationRequest(retention_duration: '{self.retention_duration}')"

    def to_json(self):
        return ucjson.dumps(
            {
                "retention_duration": self.retention_duration,
            }
        )

    @classmethod
    def from_json(cls, data):
        return cls(ColumnRetentionDuration.from_json(data["retention_duration"]))


class UpdateColumnRetentionDurationsRequest:
    retention_durations: list[ColumnRetentionDuration]

    def __init__(
        self,
        retention_durations,
    ):
        self.retention_durations = retention_durations

    def __repr__(self):
        return f"UpdateColumnRetentionDurationsRequest(retention_durations: '{self.retention_durations}')"

    def to_json(self):
        return ucjson.dumps(
            {
                "retention_durations": self.retention_durations,
            }
        )

    @classmethod
    def from_json(cls, data):
        return cls(
            [
                ColumnRetentionDuration.from_json(rd)
                for rd in data["retention_durations"]
            ]
        )


class ColumnRetentionDurationResponse:
    max_duration: RetentionDuration
    retention_duration: ColumnRetentionDuration

    def __init__(
        self,
        max_duration,
        retention_duration,
    ):
        self.max_duration = max_duration
        self.retention_duration = retention_duration

    def __repr__(self):
        return f"ColumnRetentionDurationResponse(max_duration: '{self.max_duration}', retention_duration: '{self.retention_duration}')"

    @classmethod
    def from_json(cls, data):
        return cls(
            RetentionDuration.from_json(data["max_duration"]),
            ColumnRetentionDuration.from_json(data["retention_duration"]),
        )


class ColumnRetentionDurationsResponse:
    max_duration: RetentionDuration
    retention_durations: list[ColumnRetentionDuration]

    def __init__(
        self,
        max_duration,
        retention_durations,
    ):
        self.max_duration = max_duration
        self.retention_durations = retention_durations

    def __repr__(self):
        return f"ColumnRetentionDurationsResponse(max_duration: '{self.max_duration}', retention_durations: '{self.retention_durations}')"

    @classmethod
    def from_json(cls, data):
        return cls(
            RetentionDuration.from_json(data["max_duration"]),
            [
                ColumnRetentionDuration.from_json(rd)
                for rd in data["retention_durations"]
            ],
        )


class Validator:
    id: uuid.UUID
    name: str
    function: str
    parameters: str

    def __init__(self, id, name="", function="", parameters=""):
        self.id = id
        self.name = name
        self.function = function
        self.parameters = parameters

    def __repr__(self):
        return f"Validator({self.id})"

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "function": self.function,
                "parameters": self.parameters,
            },
        )

    @classmethod
    def from_json(cls, json_data) -> Validator:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            function=json_data["function"],
            parameters=json_data["parameters"],
        )


class InspectTokenResponse:
    id: uuid.UUID
    token: str

    created: datetime.datetime
    updated: datetime.datetime

    transformer: Transformer
    access_policy: AccessPolicy

    def __init__(self, id, token, created, updated, transformer, access_policy):
        self.id = id
        self.token = token

        self.created = created
        self.updated = updated

        self.transformer = transformer
        self.access_policy = access_policy

    def to_json(self) -> str:
        return ucjson.dumps(
            {
                "id": str(self.id),
                "token": self.token,
                "created": self.created,
                "updated": self.updated,
                "transformer": self.transformer.__dict__,
                "access_policy": self.access_policy.__dict__,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, json_data) -> InspectTokenResponse:
        return cls(
            id=uuid.UUID(json_data["id"]),
            token=json_data["token"],
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            transformer=Transformer.from_json(json_data["transformer"]),
            access_policy=AccessPolicy.from_json(json_data["access_policy"]),
        )


class APIErrorResponse:
    error: str
    id: uuid.UUID
    identical: bool

    def __init__(self, error, id, identical):
        self.error = error
        self.id = id
        self.identical = identical

    def to_json(self) -> str:
        return ucjson.dumps(
            {"error": self.error, "id": self.id, "identical": self.identical}
        )

    @classmethod
    def from_json(cls, json_data: dict) -> APIErrorResponse:
        return cls(
            error=json_data["error"],
            id=uuid.UUID(json_data["id"]),
            identical=json_data["identical"],
        )


@dataclass
class Address:
    country: str | None = None
    name: str | None = None
    organization: str | None = None
    street_address_line_1: str | None = None
    street_address_line_2: str | None = None
    dependent_locality: str | None = None
    locality: str | None = None
    administrative_area: str | None = None
    post_code: str | None = None
    sorting_code: str | None = None

    @classmethod
    def from_json(cls, json_data) -> Address:
        return cls(
            country=json_data["country"],
            name=json_data["name"],
            organization=json_data["organization"],
            street_address_line_1=json_data["street_address_line_1"],
            street_address_line_2=json_data["street_address_line_2"],
            dependent_locality=json_data["dependent_locality"],
            locality=json_data["locality"],
            administrative_area=json_data["administrative_area"],
            post_code=json_data["post_code"],
            sorting_code=json_data["sorting_code"],
        )


@dataclass
class Object:
    id: uuid.UUID
    type_id: uuid.UUID
    alias: str | None = None
    created: datetime.datetime | None = None
    updated: datetime.datetime | None = None
    deleted: datetime.datetime | None = None
    organization_id: uuid.UUID | None = None

    @classmethod
    def from_json(cls, json_data) -> Object:
        return cls(
            id=uuid.UUID(json_data["id"]),
            type_id=uuid.UUID(json_data["type_id"]),
            alias=json_data.get("alias"),
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            deleted=iso8601.parse_date(json_data["deleted"]),
            organization_id=_maybe_get_org_id(json_data),
        )


@dataclass
class Edge:
    id: uuid.UUID
    edge_type_id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    created: datetime.datetime | None = None
    updated: datetime.datetime | None = None
    deleted: datetime.datetime | None = None

    @classmethod
    def from_json(cls, json_data) -> Edge:
        return cls(
            id=uuid.UUID(json_data["id"]),
            edge_type_id=uuid.UUID(json_data["edge_type_id"]),
            source_object_id=uuid.UUID(json_data["source_object_id"]),
            target_object_id=uuid.UUID(json_data["target_object_id"]),
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            deleted=iso8601.parse_date(json_data["deleted"]),
        )


@dataclass
class ObjectType:
    id: uuid.UUID
    type_name: str
    created: datetime.datetime | None = None
    updated: datetime.datetime | None = None
    deleted: datetime.datetime | None = None
    organization_id: uuid.UUID | None = None

    @classmethod
    def from_json(cls, json_data) -> ObjectType:
        return cls(
            id=uuid.UUID(json_data["id"]),
            type_name=json_data["type_name"],
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            deleted=iso8601.parse_date(json_data["deleted"]),
            organization_id=_maybe_get_org_id(json_data),
        )


@dataclass
class Attribute:
    name: str
    direct: bool
    inherit: bool
    propagate: bool

    @classmethod
    def from_json(cls, json_data) -> Attribute:
        return cls(
            name=json_data["name"],
            direct=json_data["direct"],
            inherit=json_data["inherit"],
            propagate=json_data["propagate"],
        )


@dataclass
class EdgeType:
    id: uuid.UUID
    type_name: str
    source_object_type_id: uuid.UUID
    target_object_type_id: uuid.UUID
    attributes: list[Attribute]
    created: datetime.datetime | None = None
    updated: datetime.datetime | None = None
    deleted: datetime.datetime | None = None
    organization_id: uuid.UUID | None = None

    @classmethod
    def from_json(cls, json_data: dict) -> EdgeType:
        return cls(
            id=uuid.UUID(json_data["id"]),
            type_name=json_data["type_name"],
            source_object_type_id=uuid.UUID(json_data["source_object_type_id"]),
            target_object_type_id=uuid.UUID(json_data["target_object_type_id"]),
            attributes=[
                Attribute.from_json(attr) for attr in json_data["attributes"] or []
            ],
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            deleted=iso8601.parse_date(json_data["deleted"]),
            organization_id=_maybe_get_org_id(json_data),
        )


@dataclass
class Organization:
    id: uuid.UUID
    name: str
    region: str
    created: datetime.datetime | None = None
    updated: datetime.datetime | None = None
    deleted: datetime.datetime | None = None

    @classmethod
    def from_json(cls, json_data: dict) -> Organization:
        return cls(
            id=uuid.UUID(json_data["id"]),
            name=json_data["name"],
            region=json_data["region"],
            created=iso8601.parse_date(json_data["created"]),
            updated=iso8601.parse_date(json_data["updated"]),
            deleted=iso8601.parse_date(json_data["deleted"]),
        )


def _maybe_get_org_id(json_data: dict) -> uuid.UUID | None:
    return _uuid_or_none(json_data, "organization_id")


def _uuid_or_none(json_data: dict, field: str) -> uuid.UUID | None:
    return uuid.UUID(json_data[field]) if field in json_data else None
