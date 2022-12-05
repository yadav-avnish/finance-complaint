
AWS_ACCESS_KEY_ID_ENV_KEY = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY_ENV_KEY = "AWS_SECRET_ACCESS_KEY"
MONGO_DB_URL_ENV_KEY = "MONGO_DB_URL"

import os
from dataclasses import dataclass
class EnvironmentVariable:
    mongo_db_url = os.getenv(MONGO_DB_URL_ENV_KEY)
    aws_access_key_id = os.getenv(AWS_ACCESS_KEY_ID_ENV_KEY)
    aws_secret_access_key = os.getenv(AWS_SECRET_ACCESS_KEY_ENV_KEY)


env_var = EnvironmentVariable()