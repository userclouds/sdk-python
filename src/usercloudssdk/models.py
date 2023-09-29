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

    @staticmethod
    def from_json(j):
        return UserResponse(
            uuid.UUID(j["id"]),
            datetime.datetime.fromtimestamp(j["updated_at"]),
            j["profile"],
            uuid.UUID(j["organization_id"]),
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

    @staticmethod
    def from_json(j):
        return Purpose(uuid.UUID(j["id"]), j["name"], j["description"])


class ColumnOutputConfig:
    column: ResourceID
    transformer: ResourceID

    def __init__(self, column, transformer):
        self.column = column
        self.transformer = transformer

    @staticmethod
    def from_json(j):
        return ColumnOutputConfig(
            ResourceID.from_json(j["column"]), ResourceID.from_json(j["transformer"])
        )


class Accessor:
    id: uuid.UUID
    name: str
    description: str
    columns: list[ColumnOutputConfig]
    access_policy: ResourceID
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
        version=0,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.columns = columns
        self.access_policy = access_policy
        self.selector_config = selector_config
        self.purposes = purposes
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
            }
        )

    @staticmethod
    def from_json(j):
        return Accessor(
            uuid.UUID(j["id"]),
            j["name"],
            j["description"],
            j["columns"],
            ResourceID.from_json(j["access_policy"]),
            UserSelectorConfig.from_json(j["selector_config"]),
            j["purposes"],
            j["version"],
        )


class ColumnInputConfig:
    column: ResourceID
    validator: ResourceID

    def __init__(self, column, validator):
        self.column = column
        self.validator = validator

    @staticmethod
    def from_json(j):
        return ColumnInputConfig(
            ResourceID.from_json(j["column"]), ResourceID.from_json(j["validator"])
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
                "columns": self.column_names,
                "access_policy": str(self.access_policy_id),
                "selector_config": self.selector_config.to_json(),
            }
        )

    @staticmethod
    def from_json(j):
        return Mutator(
            uuid.UUID(j["id"]),
            j["name"],
            j["description"],
            j["columns"],
            ResourceID.from_json(j["access_policy"]),
            UserSelectorConfig.from_json(j["selector_config"]),
            j["version"],
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

    @staticmethod
    def from_json(j):
        return AccessPolicyTemplate(
            uuid.UUID(j["id"]),
            j["name"],
            j["description"],
            j["function"],
            j["version"],
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

    @staticmethod
    def from_json(j):
        return AccessPolicyComponent(
            j["policy"] if "policy" in j else "",
            j["template"] if "template" in j else "",
            j["template_parameters"] if "template_parameters" in j else "",
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

    @staticmethod
    def from_json(j):
        return AccessPolicy(
            uuid.UUID(j["id"]),
            j["name"],
            j["description"],
            j["policy_type"],
            j["version"],
            [AccessPolicyComponent.from_json(c) for c in j["components"]],
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
    alias: str
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
