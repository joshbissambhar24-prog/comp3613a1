"""Integration: HTTP routing, auth, service layer and isolated SQLite persistence."""

def test_health_endpoint(client):
    assert client.get('/health').json() == {'ok': True}

def test_unauthenticated_api_is_rejected(client):
    assert client.get('/api/submissions').status_code == 401
    assert client.get('/api/users').status_code == 401

def test_student_submission_and_tracking(client, users, login_as):
    login_as(users[0])
    r = client.post('/api/submissions', json={
        'title': '  Climate Study  ', 'description': ' Coastal observations ', 'research_type': 'Poster'})
    assert r.status_code == 201, r.text
    record = r.json()
    assert record['title'] == 'Climate Study' and record['status'] == 'Pending'
    assert client.get('/api/submissions').json()[0]['id'] == record['id']
    assert client.get(f"/api/submissions/{record['id']}").status_code == 200

def test_student_cannot_access_another_students_submission(client, users, login_as):
    login_as(users[0]); r = client.post('/api/submissions', json={
        'title':'Study','description':'Notes','research_type':'Presentation'})
    assert r.status_code == 201, r.text
    sid = r.json()['id']
    login_as(users[1])
    assert client.get(f'/api/submissions/{sid}').status_code == 404
    assert client.get('/api/submissions').json() == []

def test_student_cannot_review_or_list_users(client, users, login_as):
    login_as(users[0])
    assert client.post('/api/submissions/1/reviews', json={
        'feedback': 'Approved', 'outcome': 'Accepted'}).status_code == 401
    assert client.get('/api/users').status_code == 401

def test_invalid_submission_rejected(client, users, login_as):
    login_as(users[0])
    r = client.post('/api/submissions', json={
        'title':'', 'description':'Details', 'research_type':'Poster'})
    assert r.status_code == 422
    assert client.get('/api/submissions').json() == []

def test_review_updates_submission_and_records_review(client, users, login_as, db):
    from sqlmodel import select
    from app.models.review import Review
    login_as(users[0]); created = client.post('/api/submissions', json={
        'title':'Paper','description':'Research','research_type':'Poster'})
    assert created.status_code == 201, created.text
    sid = created.json()['id']
    login_as(users[2]); reviewed = client.post(f'/api/submissions/{sid}/reviews', json={
        'feedback':'Needs more data', 'outcome':'Requires Changes'})
    assert reviewed.status_code == 201, reviewed.text
    assert reviewed.json()['outcome'] == 'Requires Changes'
    assert client.get(f'/api/submissions/{sid}').json()['status'] == 'Requires Changes'
    assert len(db.exec(select(Review)).all()) == 1

def test_reviewer_can_schedule_accepted_presentation(client, users, login_as, db):
    from sqlmodel import select
    from app.models.presentation import Presentation
    login_as(users[0]); r=client.post('/api/submissions', json={
        'title':'Demo','description':'Research', 'research_type':'Presentation'})
    assert r.status_code == 201, r.text
    sid=r.json()['id']
    login_as(users[2]); r=client.post(f'/api/submissions/{sid}/reviews', json={
        'feedback':'Approved', 'outcome':'Accepted', 'presentation_date':'2026-12-10',
        'presentation_time':'14:00', 'location':'Lecture Hall'})
    assert r.status_code == 201, r.text
    records=db.exec(select(Presentation)).all()
    assert len(records)==1 and records[0].location=='Lecture Hall'
    
def test_student_can_resubmit_after_changes_requested(
    client, users, login_as, db
):
    from app.models.submission import Submission

    # Student creates research
    login_as(users[0])
    response = client.post("/api/submissions", json={
        "title": "Original Research",
        "description": "Original description",
        "research_type": "Poster",
    })
    assert response.status_code == 201
    submission_id = response.json()["id"]

    # Reviewer requests changes
    login_as(users[2])
    response = client.post(
        f"/api/submissions/{submission_id}/reviews",
        json={
            "feedback": "Please revise your research",
            "outcome": "Requires Changes",
        },
    )
    assert response.status_code == 201

    # Student resubmits corrected research
    login_as(users[0])
    response = client.post(
        f"/submissions/{submission_id}/resubmit",
        data={
            "title": "Updated Research",
            "description": "Corrected description",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    # Verify changes were saved in the database
    db.expire_all()
    submission = db.get(Submission, submission_id)

    assert submission is not None
    assert submission.title == "Updated Research"
    assert submission.description == "Corrected description"
    assert submission.status == "Pending"