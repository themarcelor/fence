from unittest import mock


def test_list_resource_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.get_resource("/")
        assert mock_get.called_with(arborist_client._base_url + "/resource/")


def test_get_resource_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.get_resource("/a/b/c")
        assert mock_get.called_with(arborist_client._base_url + "/resource/a/b/c")


def test_create_resource_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_resource("/", {"name": "test"})
        assert mock_post.called_with(arborist_client._base_url + "/resource/")


def test_update_resource_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.put") as mock_put:
        arborist_client.update_resource("/a/b/c", {"name": "test"})
        assert mock_put.called_with(arborist_client._base_url + "/resource/a/b/c")


def test_delete_resource_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.delete") as mock_delete:
        arborist_client.delete_resource("/a/b/c")
        assert mock_delete.called_with(arborist_client._base_url + "/resource/a/b/c")

