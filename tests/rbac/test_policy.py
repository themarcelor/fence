from unittest import mock


def test_list_policies_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.list_policies()
        assert mock_get.called_with(arborist_client._base_url + "/policy/")


def test_policies_not_exist_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.policies_not_exist(["foo-bar"])
        assert mock_get.called_with(arborist_client._base_url + "/policy/")


def test_get_policy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.get") as mock_get:
        arborist_client.get_policy("/a/b/c")
        assert mock_get.called_with(arborist_client._base_url + "/policy/a/b/c")


def test_create_policy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_policy(
            {"id": "test", "resource_paths": ["/"], "role_ids": ["test"]}
        )
        assert mock_post.called_with(arborist_client._base_url + "/policy/")


def test_delete_policy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.delete") as mock_delete:
        arborist_client.delete_policy("/")
        assert mock_delete.called_with(arborist_client._base_url + "/policy/")