# Pydantic schemas validate the data we receive and respond with
# By creating these schemas, we are telling pydantic what format we are expecting to receive the data in
# as well what format the output/ response we give should have

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime





# -------------------------- USER SCHEMAS ------------------------------------------
# --------------------------------------------------------------------------------------

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
    profile_pic: str | None
    img_path: str

class UpdateUser(BaseUser):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=50)
    profile_pic: str | None = Field(default=None, min_length=1, max_length=50)




# -------------------------- CAMPAIGN SCHEMAS ------------------------------------------
# --------------------------------------------------------------------------------------

class BaseCampaign(BaseModel):

    campaign_name: str = Field(min_length = 1, max_length = 50) # Setting min value makes field required
    # author: str = Field(min_length = 1, max_length = 50) Author now comes from relationship defined in models
    campaign_details: str = Field(min_length = 1)


class CreateCampaign(BaseCampaign): # Can be used to PUT data since all fields are required
    user_id: int

class ResponseCampaign(BaseCampaign):
    model_config = ConfigDict(from_attributes=True) # Allows SQLAlchemy to use dot notation when accessing dicts

    user_id: int
    # specifying extra fields to be returned by the API in its response
    campaign_id: int
    created_at: datetime
    author: ResponseUser

class UpdateCampaign(BaseCampaign):
    campaign_name: str | None = Field(default=None, min_length = 1, max_length = 50) # | None makes field optional BUT need a default value then
    campaign_details: str | None = Field(default=None, min_length = 1)