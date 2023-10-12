import datetime
import uuid
from dataclasses import dataclass

import iso8601

from . import ucjson


class User:
    id: uuid.UUID
    profile: dict

    def __init__(self, id, profile):
        self.id = id
        self.profile = profile

    def to_json(self):
        return ucjson.dumps(
            {
                "id": str(self.id),
                "profile": self.profile,
            }
        )

    @staticmethod
    def from_json(j):
        return User(
            uuid.UUID(j["id"]),
            j["profile"],
        )


class UserResponse:
    id: uuid.UUID
    updated_at: datetime.datetime
    profile: dict
    organization_id: uuid.UUID

    def __init__(self, id, updated_at, profile, organization_id):
        self.id = id
        self.updated_at = updated_at
        self.profile = profile
        self.organization_id = organization_id

    def to_json(self):
        return ucjson.dumps(
            {
                "id": str(self.id),
                "updated_at": self.updated_at.isoformat(),
                "profile": self.profile,
                "organization_id": str(self.organization_id),
            }
        )

    @classmethod
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]),
            datetime.datetime.fromtimestamp(json_data["updated_at"]),
            json_data["profile"],
            uuid.UUID(json_data["organization_id"]),
        )


class UserSelectorConfig:
    where_clause: str

    def __init__(self, where_clause):
        self.where_clause = where_clause

    def to_json(self):
        return ucjson.dumps({"where_clause": self.where_clause})

    @staticmethod
    def from_json(j):
        return UserSelectorConfig(j["where_clause"])


class ResourceID:
    def __init__(self, id="", name=""):
        if id != "":
            setattr(self, "id", id)
        if name != "":
            setattr(self, "name", name)

    def __repr__(self):
        if hasattr(self, "id"):
            return f"ResourceID({self.id})"
        elif hasattr(self, "name"):
            return f"ResourceID({self.name})"
        else:
            return "ResourceID()"

    def isValid(self):
        return hasattr(self, "id") or hasattr(self, "name")

    @staticmethod
    def from_json(j):
        return ResourceID(j["id"], j["name"])


class Column:
    id: uuid.UUID
    name: str
    type: str
    is_array: bool
    default_value: str
    index_type: str

    def __init__(self, id, name, type, is_array, default_value, index_type):
        self.id = id
        self.name = name
        self.type = type
        self.is_array = is_array
        self.default_value = default_value
        self.index_type = index_type

    def to_json(self):
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

    @staticmethod
    def from_json(j):
        return Column(
            uuid.UUID(j["id"]),
            j["name"],
            j["type"],
            j["is_array"],
            j["default_value"],
            j["index_type"],
        )


class Purpose:
    id: uuid.UUID
    name: str
    description: str

    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

    def to_json(self):
        return ucjson.dumps(
            {"id": str(self.id), "name": self.name, "description": self.description}
        )

    @classmethod
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]), json_data["name"], json_data["description"]
        )


class ColumnOutputConfig:
    column: ResourceID
    transformer: ResourceID

    def __init__(self, column, transformer):
        self.column = column
        self.transformer = transformer

    @classmethod
    def from_json(cls, json_data):
        return ColumnOutputConfig(
            ResourceID.from_json(json_data["column"]),
            ResourceID.from_json(json_data["transformer"]),
        )


class Accessor:
    id: uuid.UUID
    name: str
    description: str
    columns: list[ColumnOutputConfig]
    access_policy: ResourceID
    token_access_policy: ResourceID
    selector_config: UserSelectorConfig
    purposes: list[ResourceID]
    version: int

    def __init__(
        self,
        id,
        name,
        description,
        columns,
        access_policy,
        selector_config,
        purposes,
        token_access_policy=None,
        version=0,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.columns = columns
        self.access_policy = access_policy
        self.selector_config = selector_config
        self.purposes = purposes
        self.token_access_policy = token_access_policy
        self.version = version

    def to_json(self):
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
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]),
            json_data["name"],
            json_data["description"],
            json_data["columns"],
            ResourceID.from_json(json_data["access_policy"]),
            UserSelectorConfig.from_json(json_data["selector_config"]),
            json_data["purposes"],
            ResourceID.from_json(json_data["token_access_policy"]),
            json_data["version"],
        )


class ColumnInputConfig:
    column: ResourceID
    validator: ResourceID

    def __init__(self, column, validator):
        self.column = column
        self.validator = validator

    @classmethod
    def from_json(cls, json_data):
        return cls(
            ResourceID.from_json(json_data["column"]),
            ResourceID.from_json(json_data["validator"]),
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
        id,
        name,
        description,
        columns,
        access_policy,
        selector_config,
        version=0,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.columns = columns
        self.access_policy = access_policy
        self.selector_config = selector_config
        self.version = version

    def to_json(self):
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
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]),
            json_data["name"],
            json_data["description"],
            json_data["columns"],
            ResourceID.from_json(json_data["access_policy"]),
            UserSelectorConfig.from_json(json_data["selector_config"]),
            json_data["version"],
        )


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
    ):
        self.id = id
        self.name = name
        self.description = description
        self.function = function
        self.version = version

    def __repr__(self):
        return f"AccessPolicyTemplate({self.id})"

    def to_json(self):
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
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]),
            json_data["name"],
            json_data["description"],
            json_data["function"],
            json_data["version"],
        )


class AccessPolicyComponent:
    def __init__(self, policy="", template="", template_parameters=""):
        if policy != "":
            setattr(self, "policy", policy)
        if template != "":
            setattr(self, "template", template)
            setattr(self, "template_parameters", template_parameters)

    def __repr__(self):
        if hasattr(self, "policy"):
            return f"AccessPolicyComponent({self.policy})"
        elif hasattr(self, "template"):
            return f"AccessPolicyComponent({self.template})"
        else:
            return "AccessPolicyComponent()"

    def to_json(self):
        obj = {}
        if self.policy:
            obj["policy"] = self.policy.to_json()
        if self.template:
            obj["template"] = self.template.to_json()
            obj["template_parameters"] = self.template_parameters
        return ucjson.dumps(obj)

    @classmethod
    def from_json(cls, json_data):
        return cls(
            json_data["policy"] if "policy" in json_data else "",
            json_data["template"] if "template" in json_data else "",
            json_data["template_parameters"]
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
    ):
        self.id = id
        self.name = name
        self.description = description
        self.policy_type = policy_type
        self.version = version
        self.components = components

    def __repr__(self):
        return f"AccessPolicy({self.id})"

    def to_json(self):
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
    def from_json(cls, json_data):
        return cls(
            uuid.UUID(json_data["id"]),
            json_data["name"],
            json_data["description"],
            json_data["policy_type"],
            json_data["version"],
            [AccessPolicyComponent.from_json(apc) for apc in json_data["components"]],
        )


class Transformer:
    id: uuid.UUID
    name: str
    input_type: str
    transform_type: str
    function: str
    parameters: str

    def __init__(
        self,
        id=uuid.UUID(int=0),
        name="",
        input_type="",
        transform_type="",
        function="",
        parameters="",
    ):
        self.id = id
        self.name = name
        self.input_type = input_type
        self.transform_type = transform_type
        self.function = function
        self.parameters = parameters

    def __repr__(self):
        return f"Transformer({self.id})"

    def to_json(self):
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "input_type": self.input_type,
                "transform_type": self.transform_type,
                "function": self.function,
                "parameters": self.parameters,
            },
        )

    @staticmethod
    def from_json(j):
        return Transformer(
            uuid.UUID(j["id"]),
            j["name"],
            j["input_type"],
            j["transform_type"],
            j["function"],
            j["parameters"],
        )


class RetentionDuration:
    unit: str
    duration: int

    def __init__(self, unit, duration):
        self.unit = unit
        self.duration = duration

    def __repr__(self):
        return f"RetentionDuration(unit: '{self.unit}', duration: '{self.duration}')"

    def to_json(self):
        return ucjson.dumps(
            {
                "unit": self.unit,
                "duration": self.duration,
            }
        )

    @classmethod
    def from_json(cls, data):
        return cls(
            data["unit"],
            data["duration"],
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

    def to_json(self):
        return ucjson.dumps(
            {
                "id": str(self.id),
                "name": self.name,
                "function": self.function,
                "parameters": self.parameters,
            },
        )

    @staticmethod
    def from_json(j):
        return Validator(uuid.UUID(j["id"]), j["name"], j["function"], j["parameters"])


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

    def to_json(self):
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

    @staticmethod
    def from_json(j):
        return InspectTokenResponse(
            uuid.UUID(j["id"]),
            j["token"],
            iso8601.parse_date(j["created"]),
            iso8601.parse_date(j["updated"]),
            Transformer.from_json(j["transformer"]),
            AccessPolicy.from_json(j["access_policy"]),
        )


class APIErrorResponse:
    error: str
    id: uuid.UUID
    identical: bool

    def __init__(self, error, id, identical):
        self.error = error
        self.id = id
        self.identical = identical

    def to_json(self):
        return ucjson.dumps(
            {"error": self.error, "id": self.id, "identical": self.identical}
        )

    @staticmethod
    def from_json(j):
        return APIErrorResponse(j["error"], j["id"], j["identical"])


@dataclass
class Address:
    country: str = None
    name: str = None
    organization: str = None
    street_address_line_1: str = None
    street_address_line_2: str = None
    dependent_locality: str = None
    locality: str = None
    administrative_area: str = None
    post_code: str = None
    sorting_code: str = None

    @classmethod
    def from_json(cls, j):
        return cls(**j)


@dataclass
class Object:
    id: uuid.UUID
    type_id: uuid.UUID
    alias: str = None
    created: datetime.datetime = None
    updated: datetime.datetime = None
    deleted: datetime.datetime = None
    organization_id: uuid.UUID = None

    @classmethod
    def from_json(cls, j):
        j["id"] = uuid.UUID(j["id"])
        j["type_id"] = uuid.UUID(j["type_id"])
        return cls(**j)


@dataclass
class Edge:
    id: uuid.UUID
    edge_type_id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    created: datetime.datetime = None
    updated: datetime.datetime = None
    deleted: datetime.datetime = None

    @classmethod
    def from_json(cls, j):
        j["id"] = uuid.UUID(j["id"])
        j["edge_type_id"] = uuid.UUID(j["edge_type_id"])
        j["source_object_id"] = uuid.UUID(j["source_object_id"])
        j["target_object_id"] = uuid.UUID(j["target_object_id"])
        return cls(**j)


@dataclass
class ObjectType:
    id: uuid.UUID
    type_name: str
    created: datetime.datetime = None
    updated: datetime.datetime = None
    deleted: datetime.datetime = None
    organization_id: uuid.UUID = None

    @classmethod
    def from_json(cls, j):
        return _from_json_with_id(cls, j)


@dataclass
class Attribute:
    name: str
    direct: bool
    inherit: bool
    propagate: bool

    @classmethod
    def from_json(cls, j):
        return cls(**j)


@dataclass
class EdgeType:
    id: uuid.UUID
    type_name: str
    source_object_type_id: uuid.UUID
    target_object_type_id: uuid.UUID
    attributes: list[Attribute]
    created: datetime.datetime = None
    updated: datetime.datetime = None
    deleted: datetime.datetime = None
    organization_id: uuid.UUID = None

    @classmethod
    def from_json(cls, j):
        j["id"] = uuid.UUID(j["id"])
        j["source_object_type_id"] = uuid.UUID(j["source_object_type_id"])
        j["target_object_type_id"] = uuid.UUID(j["target_object_type_id"])
        return cls(**j)


@dataclass
class Organization:
    id: uuid.UUID
    name: str
    region: str
    created: datetime.datetime = None
    updated: datetime.datetime = None
    deleted: datetime.datetime = None

    @classmethod
    def from_json(cls, j):
        return _from_json_with_id(cls, j)


def _from_json_with_id(cls, j):
    j["id"] = uuid.UUID(j["id"])
    return cls(**j)
