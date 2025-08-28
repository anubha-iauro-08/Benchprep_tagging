from snowflake.snowpark.functions import lit, concat, col
from base_dataframe_factory import BaseDataframeFactory

class QuestionDataframeFactory(BaseDataframeFactory):
    def __init__(self, session):
        self.session = session

    def build_first_n_tenants(self, first_n_tenants):
        questions = self.session.table(self.QUESTIONS_TABLE)
        content_packages = self.session.table(self.CONTENT_PACKAGES_TABLE)

        return (
            questions.join(
                content_packages,
                questions["CONTENT_PACKAGE_ID"] == content_packages["ID"],
            )
            .join(first_n_tenants, content_packages["TENANT_ID"] == first_n_tenants["ID"])
            .filter(questions["DELETED_AT"].is_null())
            .select(
                content_packages["TENANT_ID"].alias("TENANT_ID"),
                content_packages["TITLE"].alias("CONTENT_PACKAGE_TITLE"),
                content_packages["ID"].alias("CONTENT_PACKAGE_ID"),
                lit("question").alias("CONTENT_TYPE"),
                questions["ID"].alias("CONTENT_ID"),
                questions["ID"].alias("NAME"),
                concat(
                    questions["QUESTION_CONTENT"],
                    lit(" "),
                    questions["ANSWER_CONTENT"],
                ).alias("CONTENT"),
                questions["CONTENT_SHA"].alias("CONTENT_SHA"),
                questions["CORRECT_ANSWER"].alias("CORRECT_ANSWER"),
            )
            .sort(content_packages["TENANT_ID"], content_packages["ID"])
        )