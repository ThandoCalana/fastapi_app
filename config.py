from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
     # In this case model config tells the class where to read its data from and what encoding to use
    model_config = SettingsConfigDict(
        env_file= ".env",
        env_file_encoding= "utf-8"
    )

    # Below, we define the fields our class needs/ will expect to read from the .env file.
    # Variable names are case insensitive
    secret_key: SecretStr # need to use .get_value() to access the actual value, otherwise won't see the actual value because of data type
    algorithm: str = "HS256" # default set
    access_token_expire_minutes: int = 30 # default set

# Now, we load the environment variables into settings, from the .env file
settings = Settings() # type: ignore[call-arg]