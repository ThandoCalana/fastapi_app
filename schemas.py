from pydantic import BaseModel, Field, ConfigDict

class BaseCampaign(BaseModel):

    name: str = Field(min_length = 1, max_length = 50) # Setting min value makes field required
    author: str = Field(min_length = 1, max_length = 50)
    campaign_details: str = Field(min_length = 1)
    due_date: str = Field(min_length = 1, max_length = 50)

class CreateCampaign(BaseCampaign):
    pass

class ResponseCampaign(BaseCampaign):
    model_config = ConfigDict(from_attributes=True) # Allows Model to read dot notation when accessing dicts

    # specifying extra fields to be returned by the API in its response
    campaign_id: int
    created_at: str