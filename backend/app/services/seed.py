from app.db.session import SessionLocal
import app.models
from app.models.skill import Skill
from app.models.skill_step import SkillStep

# ==========================================================
# Starter skill catalogue.
# The project maintainer manages the catalogue here (spec 5.3).
# Run:  python -m app.services.seed   (from the backend folder)
# Skills that already exist (same name) are skipped.
# ==========================================================

CATALOGUE = [
    {
        "name": "Computer Basics",
        "category": "Digital literacy",
        "description": "Use a computer confidently: files, folders, typing and staying safe online.",
        "steps": [
            ("Turn on, log in and use the mouse and keyboard", "Practise clicking, dragging and typing a short paragraph."),
            ("Create, rename and organise folders", "Make a folder for your CV and job documents."),
            ("Save, find and open files", "Save a document, close it and find it again."),
            ("Browse the internet safely", "Search for a topic and spot an unsafe link."),
            ("Create strong passwords", "Make a password with 12+ characters and store it safely."),
        ],
    },
    {
        "name": "Email & Online Communication",
        "category": "Digital literacy",
        "description": "Write professional emails, attach documents and communicate clearly online.",
        "steps": [
            ("Create a professional email address", "Use your name, avoid nicknames."),
            ("Write a clear professional email", "Greeting, purpose, short body and sign-off."),
            ("Attach and send a document", "Attach your CV as a PDF and send it to yourself."),
            ("Reply, forward and organise your inbox", "Use folders or labels for job applications."),
        ],
    },
    {
        "name": "Microsoft Word / Google Docs",
        "category": "Office skills",
        "description": "Create and format documents such as a CV and a cover letter.",
        "steps": [
            ("Create and save a new document", "Learn the toolbar and save in .docx and PDF."),
            ("Format text, headings and lists", "Use bold, headings and bullet points."),
            ("Insert tables and images", "Add a simple table and a picture."),
            ("Build your CV", "Use headings for experience, education and skills."),
            ("Write a cover letter", "One page, tailored to a specific job."),
        ],
    },
    {
        "name": "Spreadsheets (Excel / Google Sheets)",
        "category": "Office skills",
        "description": "Enter data, use formulas and create simple charts.",
        "steps": [
            ("Enter and format data", "Rows, columns, number and date formats."),
            ("Use basic formulas", "SUM, AVERAGE, MIN and MAX."),
            ("Sort and filter data", "Sort a list and filter by a value."),
            ("Create a simple chart", "Turn a small table into a bar chart."),
            ("Build a personal budget sheet", "Track income and expenses for a month."),
            ("Use IF and VLOOKUP / XLOOKUP", "Look up values from another table."),
        ],
    },
    {
        "name": "Social Media for Business",
        "category": "Digital marketing",
        "description": "Use social media to promote a small business or your own services.",
        "steps": [
            ("Set up a business page", "Choose a platform your customers use."),
            ("Plan a weekly content calendar", "Plan 3 posts for one week."),
            ("Take and edit good photos with a phone", "Light, framing and simple edits."),
            ("Write posts that get engagement", "Clear message and a call to action."),
            ("Read basic page insights", "Reach, engagement and followers."),
        ],
    },
    {
        "name": "Introduction to Web Development",
        "category": "Tech",
        "description": "Build a simple web page with HTML, CSS and JavaScript.",
        "steps": [
            ("Understand how the web works", "Browsers, servers and URLs."),
            ("Write your first HTML page", "Headings, paragraphs, links and images."),
            ("Style the page with CSS", "Colours, fonts, spacing and layout."),
            ("Make the page work on a phone", "Use media queries and flexible layouts."),
            ("Add interaction with JavaScript", "Respond to a button click."),
            ("Publish your page online", "Use a free hosting service."),
            ("Build a portfolio page", "Show your projects and contact details."),
            ("Use Git and GitHub", "Commit and push your code."),
        ],
    },
    {
        "name": "Customer Service Skills",
        "category": "Workplace skills",
        "description": "Help customers clearly and politely in person, on the phone and online.",
        "steps": [
            ("Active listening", "Repeat back what the customer needs."),
            ("Handle a complaint calmly", "Acknowledge, apologise, solve and follow up."),
            ("Answer customer messages online", "Clear, friendly and quick replies."),
            ("Use a simple ticket or order system", "Log, update and close a request."),
        ],
    },
    {
        "name": "Interview & Job Search Skills",
        "category": "Career readiness",
        "description": "Find opportunities, apply properly and prepare for interviews.",
        "steps": [
            ("Search for jobs online", "Use filters for location and job type."),
            ("Tailor your CV to a job", "Match your skills to the requirements."),
            ("Prepare answers to common questions", "Tell me about yourself, strengths, weaknesses."),
            ("Do a practice interview", "Ask a friend or record yourself."),
            ("Follow up after an interview", "Send a short thank-you email."),
        ],
    },
]

def seed_skills(db):
    added = 0
    for item in CATALOGUE:
        exists = db.query(Skill).filter(Skill.name == item["name"]).first()
        if exists:
            continue
        skill = Skill(
            name=item["name"],
            description=item["description"],
            category=item["category"],
            is_active=True,
        )
        db.add(skill)
        db.flush()
        for index , (title , description) in enumerate(item["steps"]):
            db.add(SkillStep(
                skill_id=skill.id,
                title=title,
                description=description,
                order_index=index,
                required=True,
            ))
        added += 1
    db.commit()
    return added

def seed_if_empty():
    # Called when the server starts , only fills an empty catalogue
    db = SessionLocal()
    try:
        if db.query(Skill).count() == 0:
            added = seed_skills(db)
            print(f"[OpenLane] Added {added} skills to the catalogue")
    except Exception as error:
        db.rollback()
        print(f"[OpenLane] Could not seed the skill catalogue: {error}")
    finally:
        db.close()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        added = seed_skills(db)
        print(f"Added {added} new skills to the catalogue")
    finally:
        db.close()
