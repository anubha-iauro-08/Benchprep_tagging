import logging
from dynaconf import Dynaconf
from pathlib import Path
from snowflake_scraper import SnowflakeScraper  # adjust path

logging.basicConfig(level=logging.INFO)

def main():
 
    config = Dynaconf(
    envvar_prefix=False,  # do not require export prefix
    settings_files=[str(Path(".env").resolve())],  # explicitly load your .env file
    load_dotenv=True,
)

    print(config.get("SNOWFLAKE__ACCOUNT"))


    scraper = SnowflakeScraper(config)
    try:
        dfs = scraper.dataframes_for_first_n_tenants()
        for i, df in enumerate(dfs, start=1):
            print(f"\n=== DataFrame {i} ===")
            df.show(5)
    finally:
        scraper.close()

if __name__ == "__main__":
    main()

