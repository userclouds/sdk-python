from __future__ import annotations

import os
import uuid

from usercloudssdk.client import Client
from usercloudssdk.errors import UserCloudsSDKError
from usercloudssdk.models import Attribute, Edge, EdgeType, Object, ObjectType
from usercloudssdk.uchttpclient import (
    create_default_uc_http_client,
    create_no_ssl_http_client,
)

client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"


class SampleError(BaseException):
    def __init__(self, error: str) -> None:
        self.error = error


# These are the object types and edge types for this sample, which are DocUsers, Folders
# and Documents (object types), and View (edge types) between these object types. They
# are created in setup_authz and are used in test_authz.

DocUserObjectType = ObjectType(
    id=uuid.UUID("755410e3-97da-4acc-8173-4a10cab2c861"), type_name="DocUser"
)

GroupObjectType = ObjectType(
    id=uuid.UUID("2189aec5-e839-44b2-98d5-2cbdc7e97086"), type_name="Group"
)

FolderObjectType = ObjectType(
    id=uuid.UUID("f7478d4c-4001-4735-80bc-da136f22b5ac"), type_name="Folder"
)

DocumentObjectType = ObjectType(
    id=uuid.UUID("a9460374-2431-4771-a760-840a62e5566e"), type_name="Document"
)

UserMemberOfGroupEdgeType = EdgeType(
    id=uuid.UUID("92213717-6873-4d05-97d0-ab3126d55ed4"),
    type_name="UserMemberOfGroup",
    source_object_type_id=DocUserObjectType.id,
    target_object_type_id=GroupObjectType.id,
    attributes=[
        Attribute(name="view", direct=False, inherit=True, propagate=False),
    ],
)

UserViewFolderEdgeType = EdgeType(
    id=uuid.UUID("4c3a7c7b-aae4-4d58-8094-7a9f3d7da7c6"),
    type_name="UserViewFolder",
    source_object_type_id=DocUserObjectType.id,
    target_object_type_id=FolderObjectType.id,
    attributes=[Attribute(name="view", direct=True, inherit=False, propagate=False)],
)

GroupViewFolderEdgeType = EdgeType(
    id=uuid.UUID("95a416a5-37eb-4b59-bb3d-df9ee2d93b9b"),
    type_name="GroupViewFolder",
    source_object_type_id=GroupObjectType.id,
    target_object_type_id=FolderObjectType.id,
    attributes=[Attribute(name="view", direct=True, inherit=False, propagate=False)],
)

FolderViewFolderEdgeType = EdgeType(
    id=uuid.UUID("a2fcd885-f763-4a68-8733-3084631d2fbe"),
    type_name="FolderViewFolder",
    source_object_type_id=FolderObjectType.id,
    target_object_type_id=FolderObjectType.id,
    attributes=[Attribute(name="view", direct=False, inherit=False, propagate=True)],
)

FolderViewDocEdgeType = EdgeType(
    id=uuid.UUID("0765a607-a933-4e6b-9c07-4566fa8c2944"),
    type_name="FolderViewDoc",
    source_object_type_id=FolderObjectType.id,
    target_object_type_id=DocumentObjectType.id,
    attributes=[Attribute(name="view", direct=False, inherit=False, propagate=True)],
)


def setup_authz(client: Client) -> None:
    client.CreateObjectType(DocUserObjectType, if_not_exists=True)
    client.CreateObjectType(GroupObjectType, if_not_exists=True)
    client.CreateObjectType(DocumentObjectType, if_not_exists=True)
    client.CreateObjectType(FolderObjectType, if_not_exists=True)
    client.CreateEdgeType(UserMemberOfGroupEdgeType, if_not_exists=True)
    client.CreateEdgeType(UserViewFolderEdgeType, if_not_exists=True)
    client.CreateEdgeType(GroupViewFolderEdgeType, if_not_exists=True)
    client.CreateEdgeType(FolderViewFolderEdgeType, if_not_exists=True)
    client.CreateEdgeType(FolderViewDocEdgeType, if_not_exists=True)

    ot_ids = {ot.id for ot in client.ListObjectTypes()}
    for ot in (DocUserObjectType, DocumentObjectType, FolderObjectType):
        if ot.id not in ot_ids:
            raise SampleError(f"setup failed: object type {ot.type_name } missing")

    et_ids = {et.id for et in client.ListEdgeTypes()}
    for et in (
        UserViewFolderEdgeType,
        FolderViewFolderEdgeType,
        FolderViewDocEdgeType,
    ):
        if et.id not in et_ids:
            raise SampleError(f"setup failed: edge type {et.type_name} missing")

    # we don't do anything with organizations in this sample, but just illustrating
    # that the endpoint works
    client.ListOrganizations()


def test_authz(client: Client) -> None:
    original_obj_count = len(client.ListObjects())
    original_edge_count = len(client.ListEdges())

    objects = []
    edges = []

    try:
        user = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocUserObjectType.id, alias="user")
        )
        user = client.GetObject(user.id)  # no-op, just illustrative
        objects.append(user)

        group = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=GroupObjectType.id, alias="group")
        )
        objects.append(group)

        folder1 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=FolderObjectType.id, alias="folder1")
        )
        objects.append(folder1)

        folder2 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=FolderObjectType.id, alias="folder2")
        )
        objects.append(folder2)

        folder3 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=FolderObjectType.id, alias="folder3")
        )
        objects.append(folder3)

        doc1 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocumentObjectType.id, alias="doc1")
        )
        objects.append(doc1)

        doc2 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocumentObjectType.id, alias="doc2")
        )
        objects.append(doc2)

        doc3 = client.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocumentObjectType.id, alias="doc3")
        )
        objects.append(doc3)

        # user is member of group
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=UserMemberOfGroupEdgeType.id,
                    source_object_id=user.id,
                    target_object_id=group.id,
                )
            )
        )

        # user can view folder 1
        new_edge = client.CreateEdge(
            Edge(
                id=uuid.uuid4(),
                edge_type_id=UserViewFolderEdgeType.id,
                source_object_id=user.id,
                target_object_id=folder1.id,
            )
        )
        new_edge = client.GetEdge(new_edge.id)  # no-op, just illustrative
        edges.append(new_edge)

        # folder 1 can view doc 1
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewDocEdgeType.id,
                    source_object_id=folder1.id,
                    target_object_id=doc1.id,
                )
            )
        )

        # folder 1 can view folder 2
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewFolderEdgeType.id,
                    source_object_id=folder1.id,
                    target_object_id=folder2.id,
                )
            )
        )

        # folder 2 can view doc 2
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewDocEdgeType.id,
                    source_object_id=folder2.id,
                    target_object_id=doc2.id,
                )
            )
        )

        # folder 3 can view doc 3
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewDocEdgeType.id,
                    source_object_id=folder3.id,
                    target_object_id=doc3.id,
                )
            )
        )

        # user can view folder1
        if not client.CheckAttribute(user.id, folder1.id, "view"):
            raise SampleError("user cannot view folder1 but should be able to")

        # user can view folder2
        if not client.CheckAttribute(user.id, folder2.id, "view"):
            raise SampleError("user cannot view folder2 but should be able to")

        # user can view doc1
        if not client.CheckAttribute(user.id, doc1.id, "view"):
            raise SampleError("user cannot view doc1 but should be able to")

        # user can view doc2
        if not client.CheckAttribute(user.id, doc2.id, "view"):
            raise SampleError("user cannot view doc2 but should be able to")

        # user cannot view doc3
        if client.CheckAttribute(user.id, doc3.id, "view"):
            raise SampleError("user can view doc3 but should not be able to")

        # group can view folder3
        edges.append(
            client.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=GroupViewFolderEdgeType.id,
                    source_object_id=group.id,
                    target_object_id=folder3.id,
                )
            )
        )

        # now user can view doc3
        if not client.CheckAttribute(user.id, doc3.id, "view"):
            raise SampleError("user cannot view doc3 but should be able to")

    finally:
        for edge in edges:
            client.DeleteEdge(edge.id)

        for obj in objects:
            client.DeleteObject(obj.id)

    final_obj_count = len(client.ListObjects())
    final_edge_count = len(client.ListEdges())

    if final_obj_count != original_obj_count:
        raise SampleError("object count changed")

    if final_edge_count != original_edge_count:
        raise SampleError("edge count changed")


def cleanup(client: Client) -> None:
    user_view_et = client.GetEdgeType(
        UserViewFolderEdgeType.id
    )  # no-op, just illustrative
    client.DeleteEdgeType(user_view_et.id)
    client.DeleteEdgeType(FolderViewFolderEdgeType.id)
    client.DeleteEdgeType(FolderViewDocEdgeType.id)

    doc_ot = client.GetObjectType(DocumentObjectType.id)  # no-op, just illustrative
    client.DeleteObjectType(doc_ot.id)
    client.DeleteObjectType(DocUserObjectType.id)
    client.DeleteObjectType(FolderObjectType.id)


def run_authz_sample(client: Client) -> None:
    setup_authz(client)
    test_authz(client)
    cleanup(client)


if __name__ == "__main__":
    disable_ssl_verify = (
        os.environ.get("DEV_ONLY_DISABLE_SSL_VERIFICATION", "") == "true"
    )

    client = Client(
        url=url,
        client_id=client_id,
        client_secret=client_secret,
        client_factory=(
            create_no_ssl_http_client
            if disable_ssl_verify
            else create_default_uc_http_client
        ),
        session_name=os.environ.get("UC_SESSION_NAME"),
    )
    try:
        run_authz_sample(client)
    except UserCloudsSDKError as err:
        print(f"Client Error: {err!r}")
        exit(1)
    except SampleError as err:
        print(f"Sample Error: {err!r}")
        exit(1)
