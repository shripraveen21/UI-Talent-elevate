from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from ..config.database import engine, Base
from ..services.rbac_service import require_roles
from ..models.models import RoleEnum
import os

router = APIRouter(tags=["database-admin"])

@router.post("/api/reset-database")
async def reset_database():
    import psycopg2
    import os

    DB_USER = os.getenv("DB_USER_NAME")
    DB_PASSWORD = os.getenv("DB_USER_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    try:
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public';
        """)
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')

        # Drop all enums/types in public schema
        cursor.execute("""
            SELECT t.typname
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
        """)
        enums = cursor.fetchall()
        for enum in enums:
            enum_name = enum[0]
            cursor.execute(f'DROP TYPE IF EXISTS "{enum_name}" CASCADE;')

        conn.commit()
        cursor.close()
        conn.close()
        print("Database fully reset: all tables and enums/types dropped using psycopg2. No schema recreation.")
        return {"success": True, "message": "Database fully reset: all tables and enums/types dropped. Schema not recreated."}
    except Exception as e:
        print(f"Database reset failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database reset failed: {str(e)}")

@router.post("/api/seed-mockdata")
async def seed_mockdata():
    # Always resolve to project root (no env var)
    mockdata_path = "talentel-gc-0451edaf/talentel-gc-0451edaf-backend/ms1/app/controllers/mockdata.txt"
    if not os.path.exists(mockdata_path):
        print(f"Mock data file not found: {mockdata_path}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mockdata.txt not found")
    try:
        import psycopg2

        DB_USER = os.getenv("DB_USER_NAME")
        DB_PASSWORD = os.getenv("DB_USER_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")

        with open(mockdata_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
        # Split into individual SQL statements (naive split by ';', works for this file)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        inserted = 0
        errors = []
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        for stmt in statements:
            try:
                cursor.execute(stmt)
                inserted += 1
            except Exception as e:
                errors.append(str(e))
                print(f"Error executing statement: {stmt}\n{str(e)}")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Mock data seeded (no security). Records inserted: {inserted}. Errors: {len(errors)}")
        return {
            "success": True if inserted > 0 else False,
            "records_inserted": inserted,
            "errors": errors,
            "message": f"Inserted {inserted} records. {len(errors)} errors."
        }
    except Exception as e:
        print(f"Mock data seeding failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mock data seeding failed: {str(e)}")
