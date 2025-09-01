import logging
from typing import Any, List
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, concat, lit
from snowflake_connection_parameters_factory import SnowflakeConnectionParametersFactory
from flash_card_dataframe_factory import FlashCardDataframeFactory
from question_dataframe_factory import QuestionDataframeFactory
from reading_dataframe_factory import ReadingDataframeFactory
from base_dataframe_factory import BaseDataframeFactory

logger = logging.getLogger(__name__)


class SnowflakeScraper:
    """
    Enhanced Scraper implementation for Snowflake using Snowpark DataFrame API.
    Handles data extraction from Snowflake database with proper security measures.
    """

    def __init__(self, config: dict):
        """
        Initialize the SnowflakeDataScraper with configuration.

        Args:
            config (dict): Configuration dictionary containing Snowflake settings
                           and other options.
        """
        self.session = Session.builder.configs(
            SnowflakeConnectionParametersFactory().build(config)
        ).create()
        self.batch_size = config.get("BATCH_SIZE", 100)

    def dataframes_for_first_n_tenants(self) -> List[Any]:
        """
        Fetch flashcards, questions, and readings for the first N tenants.
        N = self.batch_size.
        """
        logger.info(f"[SnowflakeDataScraper] Fetching documents for first {self.batch_size} tenants")

        # First N tenants
        tenants = self.session.table(BaseDataframeFactory.TENANTS_TABLE)
        first_n_tenants = tenants.sort(col("ID")).limit(self.batch_size)

        # Use factories to join with first_n_tenants instead of filtering by tenant_id
        readings_df = ReadingDataframeFactory(self.session).build_first_n_tenants(first_n_tenants)
        questions_df = QuestionDataframeFactory(self.session).build_first_n_tenants(first_n_tenants)
        flash_cards_df = FlashCardDataframeFactory(self.session).build_first_n_tenants(first_n_tenants)

        return [readings_df, questions_df, flash_cards_df]
    
    def dataframes_from_snowflake_try_logic(self) -> List[Any]:
        """
        Fetch flashcards, questions, and readings with the same logic as the queries
        in snowflake_try.py (filter on _fivetran_deleted and limit 5).
        """
        logger.info(f"[SnowflakeScraper] Fetching data with logic from snowflake_try.py")

        # Replicate the query for questions
        questions_df = (
            self.session.table(BaseDataframeFactory.QUESTIONS_TABLE)
            .filter(col("_FIVETRAN_DELETED") == False)
            .limit(5)
            .select(col("QUESTION_CONTENT"), col("ANSWER_CONTENT"))
        )
        
        # Replicate the query for readings
        readings_df = (
            self.session.table(BaseDataframeFactory.READINGS_TABLE)
            .filter(col("_FIVETRAN_DELETED") == False)
            .limit(5)
            .select(col("CONTENT"))
        )

        # Replicate the query for flashcards
        flash_cards_df = (
            self.session.table(BaseDataframeFactory.FLASH_CARDS_TABLE)
            .filter(col("_FIVETRAN_DELETED") == False)
            .limit(5)
            .select(col("TERM"), col("DEFINITION"))
        )

        return [questions_df, readings_df, flash_cards_df]

    def close(self):
        """
        Close the Snowflake session and clean up resources.
        """
        if self.session:
            self.session.close()
            logger.info("Snowflake session closed successfully")
