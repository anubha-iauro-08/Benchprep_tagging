import logging
from dynaconf import Dynaconf
from pathlib import Path
from tag_extractor import Gen_AI_Tagextractor  # adjust import to your file

config = Dynaconf(
    envvar_prefix=False,  # do not require export prefix
    settings_files=[str(Path(".env").resolve())],  # explicitly load your .env file
    load_dotenv=True,
)
logging.basicConfig(level=logging.INFO)

extractor = Gen_AI_Tagextractor(config)

try:
    results = extractor.run()   # end-to-end run
    for r in results:
        print(r)
finally:
    extractor.close()