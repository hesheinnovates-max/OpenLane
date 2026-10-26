import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.progress import skill_percentage , display_percentage , skill_status , overall_percentage

# Acceptance criteria from the project spec (section 14)

def test_three_of_eight_shows_38_percent():
    assert skill_percentage(3,8) == 37.5
    assert display_percentage(skill_percentage(3,8)) == 38

def test_no_steps_does_not_divide_by_zero():
    assert skill_percentage(0,0) is None
    assert display_percentage(None) is None

def test_percentage_stays_between_0_and_100():
    assert skill_percentage(-2,5) == 0
    assert skill_percentage(9,5) == 100

def test_status_rules():
    assert skill_status(0,5,False) == "Not Started"
    assert skill_status(0,5,True) == "In Progress"
    assert skill_status(2,5,False) == "In Progress"
    assert skill_status(5,5,True) == "Completed"

def test_overall_average_of_100_50_0_is_50():
    assert overall_percentage([100,50,0]) == 50
    assert overall_percentage([]) is None
    assert overall_percentage([None,100]) == 100
