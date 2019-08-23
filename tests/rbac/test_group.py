from unittest import mock


def test_create_group_call(arborist_client, oauth_user):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_group(
            name="test_name", description="test_group", users=oauth_user
        )
        assert mock_post.called_with(arborist_client._base_url + "/group")


def test_grant_group_policy_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.grant_group_policy("test_name", "test_id")
        assert mock_post.called_with(
            arborist_client._base_url + "/group/test_name/policy"
        )
