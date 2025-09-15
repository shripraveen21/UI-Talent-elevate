# Project Rules - TalentElevate

## Tech Stack
- Backend: **FastAPI (Python)**  
- Frontend: **Angular + Tailwind CSS**  
- Database: **PostgreSQL**  

## Code Conventions
- Follow REST API design for FastAPI routes.
- Follow Angular best practices (services, components, modules).
- Use Tailwind utility classes for styling.

## Features & Domain Rules
- Collaborator/Capability leader roles must always be verified via backend before rendering privileged features.  
- Hierarchical **TechStack → Topics → Assessments → Skill Levels** must be respected in all queries and UI displays.  
- User dashboard navigation should always maintain **smooth flow** (no manual browser back needed).

## Restrictions
- **Do not run backend or frontend code.**  
- TRAE may only **edit, read, refactor, or generate new code files/components**.  
- All database queries must be checked against **models.py schema** before writing new logic.  

## Output Guidelines
- When suggesting changes, always show:
  1. File path (`frontend/src/app/...` or `backend/app/...`)  
  2. The exact modified code block  
  3. Explanation of why the change was needed  

## Testing / Flow
- Assume user will test changes manually; do not simulate runs.  
- TRAE should help create **test cases** or **mock data**, but not execute them.  
