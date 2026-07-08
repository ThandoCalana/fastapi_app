from datetime import datetime, timedelta
from random import randint
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Response, Request, status
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from schemas import CreateCampaign, ResponseCampaign
# from fastapi.routing import APIRouter

app = FastAPI()

# Mounting static folder to the app. Now, anything inside static folder is accessible
# Inputs => file path, instance of StaticFiles class using the 'static' folder, name we can use to ref in templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tells templating framework to look for our templates in the 'templates' dir/ folder 
templates = Jinja2Templates(directory="templates") 


# Another way to add an API route
# app.add_api_route(
#     methods=["GET"],
#     endpoint=get_campaigns
# ) 

# datetime.now().strftime('%Y-%m-%dT%H:%M')
now = datetime.now()
due = (now + timedelta(days=randint(1,10)))

campaigns: list[dict] = [
    {
        "campaign_id": 1,
        "name": "Vote for Change 2026",
        "author": "Barrack",
        "campaign_details": (
            "A nationwide campaign focused on increasing voter participation and "
            "promoting government transparency through community engagement events."
        ),
        "created_at": (now + timedelta(days=randint(-10,0))).strftime('%Y-%m-%d'),
        "due_date": now.strftime('%Y-%m-%d')
    },
    {
        "campaign_id": 2,
        "name": "Stronger Communities Initiative",
        "author": "Obama",
        "campaign_details": (
            "This campaign advocates for safer neighborhoods by investing in local "
            "infrastructure, community policing, and public recreation facilities."
        ),
        "created_at": (now + timedelta(days=randint(-10,0))).strftime('%Y-%m-%d'),
        "due_date": now.strftime('%Y-%m-%d')
    },
    {
        "campaign_id": 3,
        "name": "Education First Campaign",
        "author": "Donald",
        "campaign_details": (
            "Focused on improving access to quality education through increased funding "
            "for schools, teacher development, and student support programs."
        ),
        "due_date": (now + timedelta(days=randint(-10,0))).strftime('%Y-%m-%d'),
        "created_at": now.strftime('%Y-%m-%d')
    },
    {
        "campaign_id": 4,
        "name": "Clean Energy for Tomorrow",
        "author": "Trump",
        "campaign_details": (
            "Promotes the transition to renewable energy by supporting solar and wind "
            "projects while creating new green jobs across the country."
        ),
        "created_at": (now + timedelta(days=randint(-10,0))).strftime('%Y-%m-%d'),
        "due_date": now.strftime('%Y-%m-%d')
    },
    {
        "campaign_id": 5,
        "name": "Healthcare Access for All",
        "author": "Sanders",
        "campaign_details": (
            "Aims to expand affordable healthcare by increasing funding for public "
            "clinics, reducing medicine costs, and improving rural healthcare access."
        ),
        "created_at": (now + timedelta(days=randint(-10,0))).strftime('%Y-%m-%d'),
        "due_date": now.strftime('%Y-%m-%d')
    }
]

# GET endpoint for the homepage - for USER HOMEPAGE
# Stacking decorators = same response on multiple routes
# Don't even need mutliple endpoints. Can just direct request to specified
@app.get(
        path="/",
        name="home", # name so we know which unique route to access. Affects URL path user gets directed to
        include_in_schema=False # Exclude from API documentation
        ) 

@app.get(
        path="/campaigns",
        name="campaigns", 
        include_in_schema=False
        ) # Not useful for API consumption/ dev. THESE ARE ONLY HTML ENDPOINTS NOT API FUNCTIONALITY

def home(request: Request):
    # Pass campaigns dict list to be used in/on the actual html template file
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"campaigns": campaigns, "title": "Home"}
        ) 

# API HOMEPAGE ENDPOINT
@app.get(path="/api/campaigns", response_model=list[ResponseCampaign]) 

def get_campaigns():
    return campaigns



# USER CAMPAIGN PAGE ENDPOINT 
@app.get(
        path="/campaigns/{campaign_id}",
        response_model= ResponseCampaign,
        name='campaign',
        description="Get a campaign by its ID",
        include_in_schema=False
        )
def campaign_page(request: Request, campaign_id: int):

    for campaign in campaigns:
        if campaign_id == campaign.get('campaign_id'):
            title = campaign['name']
            return templates.TemplateResponse(
                request, 
                "campaign.html", 
                {"campaign": campaign, "title": title}
                )  
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No campaign Found")

# API CAMPAIGN PAGE ENDPOINT 
@app.get(
        path="/api/campaigns/{campaign_id}",
        name='campaign',
        description="Get a campaign by its ID"
        )
def read_campaign(campaign_id: int):

    for campaign in campaigns:
        if campaign_id == campaign.get('campaign_id'):
            return campaign    
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No campaign Found")       
    

@app.post(
        path="/api/campaigns",
        response_model= ResponseCampaign,
        status_code= status.HTTP_201_CREATED
        )
def create_campaign(campaign: CreateCampaign):

    new_id = max(c["campaign_id"] for c in campaigns) + 1 if campaigns else 1
    new_campaign: dict = {
        "campaign_id": new_id,
        "name": campaign.name,
        "author": campaign.author,
        "campaign_details": campaign.campaign_details,
        "due_date": campaign.due_date,
        "created_at": str(datetime.now())
    }

    campaigns.append(new_campaign)
    return new_campaign


@app.put(
        path="/campaigns/{id}", 
        status_code=status.HTTP_201_CREATED
        )
def update_campaign(id: int, body: dict):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            update: dict = {
                "campaign_id": id,
                "name": body.get('name'),
                "due_date": body.get('due_date'),
                "created_at": campaign.get("created_at")
            }

            campaigns[index] = update
            return {"update": update}
    raise HTTPException(status_code=404)

@app.delete(
        path="/campaigns/{id}"
        )
def delete_campaign(id: int):

    for index, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == id:
            campaigns.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# Using Startlette Exception Handler to catch 'all' HTTP excpetions over and above fastapi's
@app.exception_handler(StarletteHTTPException) 
def exception_handler(request: Request, exception: StarletteHTTPException):
    
    message = (
                exception.detail 
                if exception.detail 
                else "Error occurred. Please check your request and try again"
                )
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message}
        )
    
    return templates.TemplateResponse(
                request, 
                "error.html", 
                {
                    "status code": exception.status_code, 
                    "title": exception.status_code,
                    "message": message
                },
                status_code=exception.status_code
            ) 

@app.exception_handler(RequestValidationError) 
def validation_exception_handler(request: Request, exception: RequestValidationError):
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )
    
    return templates.TemplateResponse(
                request, 
                "error.html", 
                {
                    "status code": status.HTTP_422_UNPROCESSABLE_CONTENT, 
                    "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "message": "Invalid Response. Please check your input and try again."
                },
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
            )  