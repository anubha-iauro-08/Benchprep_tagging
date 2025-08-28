class SnowflakeConnectionParametersFactory:
    def build(self, config):
        return {
            "account": config["SNOWFLAKE__ACCOUNT"],
            "user": config["SNOWFLAKE__USER"],
            "authenticator": "SNOWFLAKE_JWT",
            "private_key_file": config.get("SNOWFLAKE__KEY_FILE_PATH", ""),
            "private_key_file_pwd": config.get("SNOWFLAKE__KEY_FILE_PASSWORD", ""),
            "role": config["SNOWFLAKE__ROLE"],
            "warehouse": config["SNOWFLAKE__WAREHOUSE"],
            "database": config["SNOWFLAKE__DATABASE"],
            # ⚠️ note: your env uses SCHEMA_TARGET instead of SCHEMA
            "schema": config.get("SNOWFLAKE__SCHEMA_TARGET"),
            "client_session_keep_alive": config.get("SNOWFLAKE__CLIENT_SESSION_KEEP_ALIVE", False),
        }
