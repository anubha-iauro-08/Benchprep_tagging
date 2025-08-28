from dynaconf import Dynaconf
from pathlib import Path

config = Dynaconf(
    envvar_prefix=False,  # do not require export prefix
    settings_files=[str(Path(".env").resolve())],  # explicitly load your .env file
    load_dotenv=True,
)

print("as_dict:", config.as_dict())
try:
    print("SNOWFLAKE.ACCOUNT:", config.SNOWFLAKE.ACCOUNT)
except Exception as e:
    print("SNOWFLAKE.ACCOUNT read error:", repr(e))

