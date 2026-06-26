from datetime import datetime
from random import randint
from typing import Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
# from fastapi.routing import APIRouter

app = FastAPI()
# now: datetime = datetime.now().strftime('%Y-%m-%dT%H:%M') 

# app = "Aza"
# app.add_api_route(
#     methods=["GET"],
#     endpoint=get_campaigns
# )

campaigns: list[dict] = [
    {
        "campaign_id": 1,
        "name": "Vote for Change 2026",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 2,
        "name": "Stronger Communities Initiative",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 3,
        "name": "Education First Campaign",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 4,
        "name": "Clean Energy for Tomorrow",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 5,
        "name": "Healthcare Access for All",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    }
]

# GET endpoint for the homepage
# Stacking decorators = same response on multiple routes
@app.get("/", response_class=HTMLResponse, include_in_schema=False) # Exclude from API documentation
@app.get("/campaigns", response_class=HTMLResponse, include_in_schema=False) # Not useful for API consumption/ dev
def get_campaigns():
    return f"<h1> {campaigns[0]["name"]} </h1>"



@app.get("/campaigns/{id}", response_class=HTMLResponse)
def read_campaign(id: int):
    if id > (len(campaigns)):
        raise HTTPException(status_code=404)
    else:
        return f"<h4> {campaigns[id-1]} </h4>"
        
@app.post("/campaigns")
def create_campaign(campaign: dict[str, Any]):

    new_campaign: dict[str, Any] = {
        "campaign_id": randint(100, 200),
        "name": campaign.get('name'),
        "due_date": campaign.get('due_date'),
        "created_at": datetime.now()
    }

    campaigns.append(new_campaign)
    return {"New campaign": new_campaign}


@app.put("/campaigns/{id}", status_code=201)
def update_campaign(id: int, body: dict[str, Any]):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            update: dict[str, Any] = {
                "campaign_id": id,
                "name": body.get('name'),
                "due_date": body.get('due_date'),
                "created_at": campaign.get("created_at")
            }

            campaigns[index] = update
            return {"update": update}
    raise HTTPException(status_code=404)

@app.delete("/campaigns/{id}")
def delete_campaign(id: int):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            campaigns.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404)

