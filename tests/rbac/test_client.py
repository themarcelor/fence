"""
Run some basic tests that the methods on ``ArboristClient`` actually try to hit
the correct URLs on the arborist API.
"""

from unittest import mock


from fence.rbac.client import ArboristClient


def test_healthy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.healthy()
        assert mock_get.called_with(arborist_client._base_url + "/health")


def test_create_client_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_client(
        "test_id", {"id": "test", "resource_paths": ["/"], "role_ids": ["test"]}
        )
        assert mock_post.called_with(arborist_client._base_url + "/client")


def test_update_client_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post, mock.patch("fence.rbac.client.requests.get") as mock_get:
        mock_post().status_code = 204
        arborist_client.update_client(
        "test_id", {"id": "test", "resource_paths": ["/"], "role_ids": ["test"]}
        )
        assert mock_get.called_with(
            arborist_client._base_url + "/client/test_id/policy"
        )
        assert mock_post.called_with(
            arborist_client._base_url + "/client/test_id/policy"
        )


def test_delete_client_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.delete") as mock_delete:
        arborist_client.delete_client("test_id")
        assert mock_delete.called_with(arborist_client._base_url + "/client/test_id")