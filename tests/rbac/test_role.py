from unittest import mock


def test_create_role_call(arborist_client):
    with mock.patch("fence.rbac.client.requests.post") as mock_post:
        arborist_client.create_role({"id": "test"})
        assert mock_post.called_with(arborist_client._base_url + "/role/")
