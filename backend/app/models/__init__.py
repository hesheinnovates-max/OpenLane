# Import every model so that Base.metadata knows about all the tables
from app.models.job_seeker import JobSeeker
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.companies import Company
from app.models.business import Business
from app.models.job import Job
from app.models.applications import Application
from app.models.skill import Skill
from app.models.skill_step import SkillStep
from app.models.job_seeker_skill import JobSeekerSkill
from app.models.step_progress import StepProgress
from app.models.course import Course
from app.models.learning_progress import LearningProgress
from app.models.reset_password import PasswordReset
