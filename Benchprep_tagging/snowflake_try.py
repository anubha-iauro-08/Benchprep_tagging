import os
from cryptography.hazmat.primitives import serialization
import snowflake.connector

private_key_file = "/home/iauro/Benchprep_tagging/aitutor_rsa_key.p8"
private_key_file_pwd = 

# Load private key
with open(private_key_file, "rb") as key_file:
    p_key = serialization.load_pem_private_key(
        key_file.read(),
        password=private_key_file_pwd.encode()
    )

private_key = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Establish connection
conn = snowflake.connector.connect(
    user='svc_ai_tutor_dev_user',
    account='wga93983',
    private_key=private_key,
    authenticator='SNOWFLAKE_JWT',
    warehouse='COMPUTE_WH',
    database='RAW_DATA_LANDING',
    schema='WMX_API_ALL_TABLES'
)

cursor = conn.cursor()
print("Connected to Snowflake")


queries = {
    "questions": """
        SELECT question_content, answer_content
        FROM questions
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """,
    "readings": """
        SELECT content
        FROM readings
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """,
    "flashcards": """
        SELECT term, definition
        FROM flash_cards
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """,
    "courses": """
        SELECT title, description
        FROM searchable_course_data
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """,
    "passages": """
        SELECT name
        FROM passages
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """,
    "passage_versions": """
        SELECT content
        FROM passage_versions
        WHERE _fivetran_deleted = FALSE
        LIMIT 5
    """
}
    
try:
    for label, query in queries.items():
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"\n=== {label.upper()} ===")
        for row in results:
            print(row)

finally:
    cursor.close()
    conn.close()
    print("Connection closed")
