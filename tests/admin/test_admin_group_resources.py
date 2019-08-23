import fence.resources.admin as adm
from fence.models import Group


def test_get_all_group(db_session, awg_users):
    # test get all groups and info
    info = adm.get_all_groups(db_session)
    assert len(info["groups"]) == 2
    names = [group["name"] for group in info["groups"]]
    assert "test_group_1" in names
    assert "test_group_2" in names
    descriptions = [group["description"] for group in info["groups"]]
    assert "the first test group" in descriptions
    assert "the second test group" in descriptions
    projects = [group["projects"] for group in info["groups"]]
    assert ["test_project_1"] in projects
    assert ["test_project_1", "test_project_2"] in projects


def test_add_empty_project_to_group(db_session, awg_users):
    # test adding empty project does not affect group projects
    group = db_session.query(Group).filter_by(name="test_group_1").first()
    assert group.name == "test_group_1"
    adm.add_projects_to_group(db_session, "test_group_1", projects=[])
    info = adm.get_group_info(db_session, "test_group_1")
    assert len(info["projects"]) == 1
    assert info["projects"] == ["test_project_1"]
