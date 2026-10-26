import math

# ==========================================================
# Progress rules (Project spec section 7)
# ==========================================================

NOT_STARTED = "Not Started"
IN_PROGRESS = "In Progress"
COMPLETED = "Completed"

def skill_percentage(completed_steps,total_steps):
    # (completed required steps / total required steps) * 100
    # Returns None when the skill has no steps , we never divide by zero or invent a number
    if total_steps <= 0:
        return None
    completed_steps = max(0,min(completed_steps,total_steps))
    return (completed_steps / total_steps) * 100

def display_percentage(percentage):
    # Round to the nearest whole number , 37.5 shows as 38
    if percentage is None:
        return None
    return int(math.floor(percentage + 0.5))

def skill_status(completed_steps,total_steps,started):
    if total_steps > 0 and completed_steps >= total_steps:
        return COMPLETED
    if started or completed_steps > 0:
        return IN_PROGRESS
    return NOT_STARTED

def overall_percentage(percentages):
    # Average of the selected skills that have steps defined
    values = [p for p in percentages if p is not None]
    if not values:
        return None
    return sum(values) / len(values)
