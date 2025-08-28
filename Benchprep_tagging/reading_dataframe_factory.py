from snowflake.snowpark.functions import lit, col
from base_dataframe_factory import BaseDataframeFactory

class ReadingDataframeFactory(BaseDataframeFactory):
    def __init__(self, session):
        self.session = session

    def build_first_n_tenants(self, first_n_tenants):
        readings = self.session.table(self.READINGS_TABLE)
        content_packages = self.session.table(self.CONTENT_PACKAGES_TABLE)
        sections = self.session.table(self.SECTIONS_TABLE)

        return (
            readings.join(
                content_packages,
                readings["CONTENT_PACKAGE_ID"] == content_packages["ID"],
            )
            .join(sections, readings["SECTION_ID"] == sections["ID"])
            .join(first_n_tenants, content_packages["TENANT_ID"] == first_n_tenants["ID"])
            .filter(readings["DELETED_AT"].is_null())
            .select(
                content_packages["TENANT_ID"].alias("TENANT_ID"),
                content_packages["TITLE"].alias("CONTENT_PACKAGE_TITLE"),
                content_packages["ID"].alias("CONTENT_PACKAGE_ID"),
                lit("reading").alias("CONTENT_TYPE"),
                readings["ID"].alias("CONTENT_ID"),
                sections["NAME"].alias("NAME"),
                readings["CONTENT"].alias("CONTENT"),
                sections["CONTENT_SHA"].alias("CONTENT_SHA"),
                sections["ID"].alias("PARENT_CONTENT_ID"),
            )
            .sort(content_packages["TENANT_ID"], content_packages["ID"])
        )