import os
import sys
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


    scraper = None
    try:
        # Instantiate the SnowflakeScraper
        scraper = SnowflakeScraper(config)

        # Call the new method to get the dataframes
        dataframes = scraper.dataframes_from_snowflake_try_logic()

        # Iterate through the dataframes and print the results
        for df in dataframes:
            df.show()

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    finally:
        # Close the session
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()

