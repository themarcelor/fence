from unittest import mock


def test_create_user_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_user({"name": "test_name"})
        assert mock_post.called_with(arborist_client._base_url + "/user/")


def test_create_user_if_not_exist_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_user_if_not_exist("test_name")
        assert mock_post.called_with(arborist_client._base_url + "/user/")


def test_grant_user_policy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.grant_user_policy(
            "test_name", {"id": "test", "resource_paths": ["/"], "role_ids": ["test"]}
        )
        assert mock_post.called_with(arborist_client._base_url + "/user/test_name/policy")


def test_revoke_all_policies_for_user(arborist_client):
    with mock.patch("fence.rbac.client.requests.delete") as mock_delete:
        arborist_client.revoke_all_policies_for_user("test_name")
        assert mock_delete.called_with(arborist_client._base_url + "/user/test_name/policy")
