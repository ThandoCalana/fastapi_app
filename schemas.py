# Pydantic schemas validate the data we receive and respond with
# By creating these schemas, we are telling pydantic what format we are expecting to receive the data in
# as well what format the output/ response we give should have

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class BaseUser(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=50)
    # password will be added later
class CreateUser(BaseUser):
    # password will be added later
    pass

class ResponseUser(BaseUser):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    campaigns: list[dict]


class BaseCampaign(BaseModel):

    campaign_name: str = Field(min_length = 1, max_length = 50) # Setting min value makes field required
    author: str = Field(min_length = 1, max_length = 50)
    campaign_details: str = Field(min_length = 1)
    created_at: str = Field(min_length = 1, max_length = 50)

class CreateCampaign(BaseCampaign):
    pass

class ResponseCampaign(BaseCampaign):
    model_config = ConfigDict(from_attributes=True) # Allows SQLAlchemy to use dot notation when accessing dicts

    # specifying extra fields to be returned by the API in its response
    campaign_id: int
    created_at: str