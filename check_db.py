import os
import django
from django.conf import settings
from django.db import connection

# --- setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transport_project.settings")
django.setup()

def show_table_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        columns = cursor.fetchall()
        if not columns:
            print(f"Table '{table_name}' introuvable dans la base {connection.settings_dict['NAME']}.")
            return
        print(f"\nBase utilisée : {connection.settings_dict['NAME']}")
        print(f"Table : {table_name}")
        print("-" * 50)
        for col_name, data_type, nullable in columns:
            print(f"{col_name:<20} | {data_type:<20} | nullable: {nullable}")
        print("-" * 50)

if __name__ == "__main__":
    print(f"DEBUG = {settings.DEBUG}, IS_RAILWAY = {os.getenv('RAILWAY_ENVIRONMENT','False')}")
    show_table_columns("etude_marche_questionnaire")
