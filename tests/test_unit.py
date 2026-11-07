"""Unit tests: validation/service behaviour with mocked repositories."""
from unittest.mock import Mock
import pytest
from app.services.submission_service import SubmissionService
from app.services.review_service import ReviewService
from app.models.submission import Submission
from app.utilities.security import encrypt_password, verify_password

@pytest.mark.parametrize('value', ['Poster', 'Presentation'])
def test_valid_research_types(value):
    SubmissionService._validate_research_type(value)

@pytest.mark.parametrize('value', ['', 'Report', 'poster'])
def test_invalid_research_types(value):
    with pytest.raises(ValueError, match='Research type'):
        SubmissionService._validate_research_type(value)

@pytest.mark.parametrize('title,description', [('', 'Description'), ('Title', '  '), ('  ', 'D')])
def test_missing_submission_details(title, description):
    with pytest.raises(ValueError):
        SubmissionService._validate_submission_details(title, description)

def test_valid_submission_details():
    SubmissionService._validate_submission_details('Title', 'Description')

def test_password_is_hashed_and_verified():
    hashed = encrypt_password('ValidPassword123!')
    assert hashed != 'ValidPassword123!'
    assert verify_password('ValidPassword123!', hashed)
    assert not verify_password('wrong', hashed)

def test_review_rejects_empty_feedback():
    with pytest.raises(ValueError, match='Feedback'):
        ReviewService(Mock()).create_review(submission_id=1, reviewer_id=2,
            feedback=' ', outcome='Accepted', presentation_date=None,
            presentation_time=None, location=None)

def test_review_rejects_incomplete_presentation():
    with pytest.raises(ValueError, match='all required'):
        ReviewService(Mock()).create_review(submission_id=1, reviewer_id=2,
            feedback='Good', outcome='Accepted', presentation_date='2026-11-15',
            presentation_time=None, location='Lab')

def test_review_rejects_presentation_on_rejection():
    with pytest.raises(ValueError, match='only be set'):
        ReviewService(Mock()).create_review(submission_id=1, reviewer_id=2,
            feedback='Needs revision', outcome='Rejected', presentation_date='2026-11-15',
            presentation_time='10:00', location='Room 1')

def test_review_updates_status_and_delegates_repository():
    repo = Mock()
    repo.get_submission.return_value = Submission(id=7, student_id=1, title='T',
        description='D', research_type='Poster', status='Pending')
    repo.save_review.side_effect = lambda review, submission, presentation: review
    result = ReviewService(repo).create_review(submission_id=7, reviewer_id=3,
        feedback=' Nice ', outcome='Requires Changes', presentation_date=None,
        presentation_time=None, location=None)
    assert result.feedback == 'Nice'
    assert repo.get_submission.return_value.status == 'Requires Changes'
    repo.save_review.assert_called_once()
