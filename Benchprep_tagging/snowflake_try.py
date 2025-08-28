import json
import os
from typing import List, Dict, Any
from cryptography.hazmat.primitives import serialization
import snowflake.connector

# private_key_file = "/home/hemant/PycharmProjects/PythonProject/Benchprep/graph_db_project/aitutor_rsa_key.p8"
private_key_file = "/home/iauro/Benchprep_tagging/aitutor_rsa_key.p8"
private_key_file_pwd = "qktCq7HC8W779!hLz@!i"

print(private_key_file)
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


# print("+++++++++++",private_key)

conn = snowflake.connector.connect(
    user='svc_ai_tutor_dev_user',
    account='wga93983',
    private_key=private_key,
    authenticator='SNOWFLAKE_JWT',
    warehouse='COMPUTE_WH',
    database='RAW_DATA_LANDING',
    schema='WMX_API_ALL_TABLES'
)

cnn=conn.cursor()
print("connected to snowflake ")

try :
    query="""SELECT
  cp.id AS content_package_id,
  cp.title AS course_title,
  cp.description AS course_description,
  cp.content_type_id,
  cp.course_type,
  s.id AS section_id,
  s.name AS section_name,
  s.content_location AS section_content_location,
  s.content_sha AS section_content_hash,
  scd.subject,
  scd.keywords AS content_tags,
  scd.summary AS content_summary,
  q.question_content,
  q.content_location AS question_content_location,
  q.content_preview,
  q.metadata AS additional_content_metadata
FROM
  content_packages AS cp
  LEFT JOIN sections AS s ON cp.id = s.content_package_id
  LEFT JOIN searchable_course_data AS scd ON cp.id = scd.content_package_id
  LEFT JOIN questions AS q ON cp.id = q.content_package_id
WHERE
  cp._fivetran_deleted = FALSE
  AND (
    s._fivetran_deleted = FALSE
    OR s._fivetran_deleted IS NULL
  )
  AND (
    scd._fivetran_deleted = FALSE
    OR scd._fivetran_deleted IS NULL
  )
  AND (
    q._fivetran_deleted = FALSE
    OR q._fivetran_deleted IS NULL
  )
ORDER BY
  cp.id,
  s.sort_order LIMIT 100;"""
    cnn.execute(query)
    for row in cnn:
        print(row)
finally:
    cnn.close()