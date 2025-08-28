from snowflake.snowpark.functions import lit, col
from base_dataframe_factory import BaseDataframeFactory

class FlashCardDataframeFactory(BaseDataframeFactory):
    def __init__(self, session):
        self.session = session

    def build_first_n_tenants(self, first_n_tenants):
        flash_cards = self.session.table(self.FLASH_CARDS_TABLE)
        content_packages = self.session.table(self.CONTENT_PACKAGES_TABLE)

        return (
            flash_cards.join(
                content_packages,
                flash_cards["CONTENT_PACKAGE_ID"] == content_packages["ID"],
            )
            .join(first_n_tenants, content_packages["TENANT_ID"] == first_n_tenants["ID"])
            .filter(flash_cards["DELETED_AT"].is_null())
            .select(
                content_packages["TENANT_ID"].alias("TENANT_ID"),
                content_packages["TITLE"].alias("CONTENT_PACKAGE_TITLE"),
                content_packages["ID"].alias("CONTENT_PACKAGE_ID"),
                lit("flashcard").alias("CONTENT_TYPE"),
                flash_cards["ID"].alias("CONTENT_ID"),
                flash_cards["TERM"].alias("NAME"),
                flash_cards["DEFINITION"].alias("CONTENT"),
                flash_cards["CONTENT_SHA"].alias("CONTENT_SHA"),
            )
            .sort(content_packages["TENANT_ID"], content_packages["ID"])
        )
