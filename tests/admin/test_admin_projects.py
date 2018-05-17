import fence.resources.admin as adm
from fence.models import Project, Bucket, ProjectToBucket


def test_get_project(db_session, awg_users):
    info = adm.get_project_info(db_session, "test_project_1")
    assert info['name'] == 'test_project_1'


def test_get_all_projects(db_session, awg_users):
    projects = adm.get_all_projects(db_session)['projects']
    info = {
        project['name']: {
            'auth_id': project['auth_id'],
            'name': project['name'],
            'associated buckets': project['associated buckets'],
            'description': project['description']
        } 
        for project in projects
    }
    expected = {
        'test_project_1': {
            'auth_id': u'phs_project_1',
            'associated buckets': [],
            'description': None,
            'name': u'test_project_1'
        },
        'test_project_2': {
            'auth_id': u'phs_project_2',
            'associated buckets': [],
            'description': None,
            'name': u'test_project_2'
        }
    }
    assert info  == expected


def test_create_project(db_session, awg_users):
    project = db_session.query(Project).filter_by(name='test_project_for_creation').first()
    assert project == None
    adm.create_project(db_session, "test_project_for_creation", "test_project_for_creation_auth_id", [])
    project = db_session.query(Project).filter_by(name='test_project_for_creation').first()
    assert project.name == "test_project_for_creation"
    assert project.auth_id == "test_project_for_creation_auth_id"
    assert project.storage_access == []


def test_delete_project(db_session, awg_users):
    project = db_session.query(Project).filter_by(name='test_project_1').first()
    assert project.name == "test_project_1" 
    adm.delete_project(db_session, "test_project_1")
    project = db_session.query(Project).filter_by(name='test_project_1').first()
    assert project == None


def test_create_bucket_in_project(db_session, awg_users, providers):
    adm.create_bucket_on_project(db_session, 'test_project_1', 'new_bucket', 'test-cleversafe')
    project = db_session.query(Project).filter_by(name='test_project_1').first()
    bucket = db_session.query(Bucket).filter_by(name='new_bucket').first()
    bucket_in_project = db_session.query(ProjectToBucket).filter_by(bucket_id=bucket.id, project_id=project.id).first()
    assert bucket_in_project.id == 1
