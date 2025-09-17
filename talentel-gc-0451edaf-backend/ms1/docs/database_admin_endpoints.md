# Database Admin Endpoints Documentation

## Endpoints

### 1. `/api/reset-database` (POST)
**Purpose:**  
Resets the database by dropping all tables and recreating the schema.

**Request:**
- Method: POST
- URL: `/api/reset-database`
- Body:  
  ```json
  { "action": "reset" }
  ```

**Response:**
- Success:  
  ```json
  { "success": true, "message": "Database reset successfully." }
  ```
- Failure:  
  ```json
  { "success": false, "message": "Database reset failed: <error>" }
  ```

**Security:**  
- No authentication or authorization required.
- Anyone can access this endpoint.

---

### 2. `/api/seed-mockdata` (POST)
**Purpose:**  
Seeds the database with mock data from `mockdata.txt`.

**Request:**
- Method: POST
- URL: `/api/seed-mockdata`
- Body: None

**Response:**
- Success:  
  ```json
  {
    "success": true,
    "records_inserted": <number>,
    "errors": [],
    "message": "Inserted <number> records. 0 errors."
  }
  ```
- Failure:  
  ```json
  {
    "success": false,
    "records_inserted": 0,
    "errors": [ "<error details>" ],
    "message": "Inserted 0 records. <number> errors."
  }
  ```

**Security:**  
- No authentication or authorization required.
- Anyone can access this endpoint.

---

## Security

- No authentication or authorization required.
- Both endpoints are open and can be accessed by anyone.
- All actions are logged for traceability.

---

## Mock Data Format (`mockdata.txt`)

- The file should contain raw SQL `INSERT INTO ...` statements for all relevant tables.
- Multi-row inserts and sub-selects are supported.
- Example tables: `employees`, `tech_stack`, `topics`, `quizzes`, `debug_exercises`, `hands_on`, `tests`, `collaborators`, `test_assign`, `quiz_results`, `debug_results`, `hands_on_results`, `employee_skills`, `skill_upgrades`, `suggestions`.
- Each statement should end with a semicolon (`;`).
- Comments (lines starting with `--`) are ignored.

**Example:**
```sql
-- Insert mock data for employees
INSERT INTO employees (name, email, hashed_password, role, band, tech_stack, manager_id) VALUES
('John Doe', 'pm@example.com', '<hashed_password>', 'ProductManager', 'B2', '{"skills": ["Python", "Java"]}', NULL);
```

---

## Error Handling

- If `mockdata.txt` is missing, a 404 error is returned.
- If any SQL statement fails, the error is logged and included in the response.
- The response includes the number of records inserted and any errors encountered.

---

## Logging

- All actions (reset, seed) are logged with user info and result.
- For production, replace `print()` statements with a proper logging framework.
