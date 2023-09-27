import uuid

from usercloudssdk.client import Client, Error
from usercloudssdk.models import Attribute, Edge, EdgeType, Object, ObjectType

client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"


class SampleError(BaseException):
    def __init__(self, error):
        self.error = error


# These are the object types and edge types for this sample, which are DocUsers, Folders
# and Documents (object types), and View (edge types) between these object types. They
# are created in setup_authz and are used in test_authz.

DocUserObjectType = ObjectType(
    id=uuid.UUID("755410e3-97da-4acc-8173-4a10cab2c861"), type_name="DocUser"
)

FolderObjectType = ObjectType(
    id=uuid.UUID("f7478d4c-4001-4735-80bc-da136f22b5ac"), type_name="Folder"
)

DocumentObjectType = ObjectType(
    id=uuid.UUID("a9460374-2431-4771-a760-840a62e5566e"), type_name="Document"
)

UserViewFolderEdgeType = EdgeType(
    id=uuid.UUID("4c3a7c7b-aae4-4d58-8094-7a9f3d7da7c6"),
    type_name="UserViewFolder",
    source_object_type_id=DocUserObjectType.id,
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


def setup_authz(c: Client):
    c.CreateObjectType(DocUserObjectType, if_not_exists=True)
    c.CreateObjectType(DocumentObjectType, if_not_exists=True)
    c.CreateObjectType(FolderObjectType, if_not_exists=True)
    c.CreateEdgeType(UserViewFolderEdgeType, if_not_exists=True)
    c.CreateEdgeType(FolderViewFolderEdgeType, if_not_exists=True)
    c.CreateEdgeType(FolderViewDocEdgeType, if_not_exists=True)

    ot_ids = {ot.id for ot in c.ListObjectTypes()}
    for ot in (DocUserObjectType, DocumentObjectType, FolderObjectType):
        if ot.id not in ot_ids:
            raise SampleError("setup failed: object type " + ot.type_name + " missing")

    et_ids = {et.id for et in c.ListEdgeTypes()}
    for et in (
        UserViewFolderEdgeType,
        FolderViewFolderEdgeType,
        FolderViewDocEdgeType,
    ):
        if et.id not in et_ids:
            raise SampleError("setup failed: edge type " + et.type_name + " missing")

    # we don't do anything with organizations in this sample, but just illustrating
    # that the endpoint works
    c.ListOrganizations()


def test_authz(c: Client):
    objects = []
    edges = []

    try:
        user = c.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocUserObjectType.id, alias="user")
        )
        objects.append(user)

        folder1 = c.CreateObject(
            Object(id=uuid.uuid4(), type_id=FolderObjectType.id, alias="folder1")
        )
        objects.append(folder1)

        folder2 = c.CreateObject(
            Object(id=uuid.uuid4(), type_id=FolderObjectType.id, alias="folder2")
        )
        objects.append(folder2)

        doc1 = c.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocumentObjectType.id, alias="doc1")
        )
        objects.append(doc1)

        doc2 = c.CreateObject(
            Object(id=uuid.uuid4(), type_id=DocumentObjectType.id, alias="doc2")
        )
        objects.append(doc2)

        edges.append(
            c.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=UserViewFolderEdgeType.id,
                    source_object_id=user.id,
                    target_object_id=folder1.id,
                )
            )
        )

        edges.append(
            c.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewFolderEdgeType.id,
                    source_object_id=folder1.id,
                    target_object_id=folder2.id,
                )
            )
        )

        edges.append(
            c.CreateEdge(
                Edge(
                    id=uuid.uuid4(),
                    edge_type_id=FolderViewDocEdgeType.id,
                    source_object_id=folder2.id,
                    target_object_id=doc2.id,
                )
            )
        )

        # user can view folder1
        if not c.CheckAttribute(user.id, folder1.id, "view"):
            raise SampleError("user cannot view folder1 but should be able to")

        # user can view folder2
        if not c.CheckAttribute(user.id, folder2.id, "view"):
            raise SampleError("user cannot view folder2 but should be able to")

        # user cannot view doc1
        if c.CheckAttribute(user.id, doc1.id, "view"):
            raise SampleError("user can view doc1 but should not be able to")

        # user can view doc2
        if not c.CheckAttribute(user.id, doc2.id, "view"):
            raise SampleError("user cannot view doc2 but should be able to")

    finally:
        for e in edges:
            c.DeleteEdge(e.id)

        for o in objects:
            c.DeleteObject(o.id)


def cleanup(c: Client):
    c.DeleteEdgeType(UserViewFolderEdgeType.id)
    c.DeleteEdgeType(FolderViewFolderEdgeType.id)
    c.DeleteEdgeType(FolderViewDocEdgeType.id)
    c.DeleteObjectType(DocUserObjectType.id)
    c.DeleteObjectType(DocumentObjectType.id)
    c.DeleteObjectType(FolderObjectType.id)


if __name__ == "__main__":
    c = Client(url, client_id, client_secret)

    try:
        setup_authz(c)
        test_authz(c)
        cleanup(c)
    except Error as e:
        print("Client Error: " + e.error)
        exit(1)
    except SampleError as e:
        print("Sample Error: " + e.error)
        exit(1)
