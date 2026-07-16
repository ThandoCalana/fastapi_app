from datetime import datetime, timedelta
from random import randint
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Response, Request, status, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Annotated
from schemas import CreateCampaign, ResponseCampaign, UpdateCampaign, CreateUser, ResponseUser, UpdateUser

from database import get_db, engine, Base
import models
# from fastapi.routing import APIRouter

Base.metadata.create_all(bind=engine) # Looks at all models inheriting from Base and creates them if they don't exist

app = FastAPI()

# Mounting static folder to the app. Now, anything inside static folder is accessible
# Inputs => file path, instance of StaticFiles class using the 'static' folder, name we can use to ref in templates
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

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


# --------------------------------------------------------------------------------------------------------
# -------------------------------------------  GET ENDPOINTS   -------------------------------------------
# --------------------------------------------------------------------------------------------------------

# GET endpoint for the homepage - for frontend user
# Stacking decorators = same response on multiple routes
# Don't even need mutliple endpoints. Can just direct request to specified
# Separation of 'API' and 'HTML' endpoints is not essentail.
# One renders the HTML for the enduser, the other returns JSON for BE user
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

def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    query = db.execute(select(models.Campaigns))
    campaigns = query.scalars()

    # Pass campaigns dict list to be used in/on the actual html template file
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"campaigns": campaigns, "title": "Home"}
        ) 


# [API] HOMEPAGE ENDPOINT
@app.get(path="/api/campaigns", response_model=list[ResponseCampaign]) 

def get_campaigns(db: Annotated[Session, Depends(get_db)]):
    query = db.execute(select(models.Campaigns).group_by(models.Users.username))
    campaigns = query.scalars().first() # selects one or none, Returns None
    # campaigns = query.scalar_one() raises an error if nothing is found

    return campaigns


# [API] Fecth all users - Only API, why would users get access to view site users?
@app.get(path="/api/users", response_model=list[ResponseUser]) 

def get_users(db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Users))
    users = result.scalars()

    if users:
        return users
    return "No users found"


# [API] Fecth current user's campaigns
@app.get(path="/api/users/{user_id}/campaigns", response_model=list[ResponseUser]) 

def user_campaigns(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user_check = db.execute(select(models.Users).where(models.Users.user_id==user_id))
    user_check_result = user_check.scalars().first()
    
    if user_check_result:
        result = db.execute(select(models.Users.campaigns).where(models.Users.user_id==user_id))
        campaigns = result.scalars()

        if campaigns:
            return campaigns
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found")
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# [HTML] Fetch current user's campaigns
@app.get(path="/users/{user_id}/campaigns", name="user_campaigns") 

def get_user_campaigns(request: Request, user_id: int, db: Annotated[Session, Depends(get_db)]):
    user_check = db.execute(select(models.Users).where(models.Users.user_id==user_id))
    user_check_result = user_check.scalars().first()
    
    if user_check_result:
        result = db.execute(select(models.Users.campaigns).where(models.Users.user_id==user_id))
        campaigns = result.scalars()

        if campaigns:
            return templates.TemplateResponse(
                    request=request,
                    name="user_campaigns.html",
                    context={"campaigns": campaigns, "title": "User Campaigns"}
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found")
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# [HTML] GET CAMPAIGNS BY ID
@app.get(
        path="/campaigns/{campaign_id}",
        response_model= ResponseCampaign,
        name='campaign',
        description="Get a campaign by its ID",
        include_in_schema=False
        )
def campaign_page(request: Request, campaign_id: int, db: Annotated[Session, Depends(get_db)]):

    results = db.execute(select(models.Campaigns).where(models.Campaigns.campaign_id==campaign_id))
    campaigns = results.scalars()

    for campaign in campaigns:
        if campaign_id == campaign.campaign_id:
            title = campaign.campaign_name
            return templates.TemplateResponse(
                request, 
                "campaign.html", 
                {"campaign": campaign, "title": title}
                )  
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No campaign Found")


# --------------------------------------------------------------------------------------------------------
# -------------------------------------------  POST ENDPOINTS   ------------------------------------------
# --------------------------------------------------------------------------------------------------------

# [API] Create user
@app.post(
        path="/api/users",
        response_model= ResponseUser,
        status_code= status.HTTP_201_CREATED
        )
def create_user(user: CreateUser, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Users.user_id).where(models.Users.email==user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    new_user = models.Users(
        username=user.username,
        email=user.email
        )
    
    db.add(new_user)
    db.commit()
    return new_user

# [API] Create new campaign
@app.post(
        path="/api/campaigns",
        response_model= ResponseCampaign,
        status_code= status.HTTP_201_CREATED
        )
def create_campaign(campaign: CreateCampaign, db: Annotated[Session, Depends(get_db)]):

    new_campaign = models.Campaigns(
        campaign_name=campaign.campaign_name,
        user_id = campaign.user_id,
        campaign_details=campaign.campaign_details,
        created_at=datetime.now()
    )

    db.add(new_campaign)
    db.commit()

    return new_campaign

# --------------------------------------------------------------------------------------------------------
# -------------------------------------------   PUT ENDPOINTS   ------------------------------------------
# --------------------------------------------------------------------------------------------------------

# [API] PUT ENDPOINT TO UPDATE A CAMPAIGN BY ID
@app.put(path="/api/campaigns/{campaign_id}", response_model=list[ResponseUser]) 

def update_campaign_full(campaign_id: int, campaign_data: CreateCampaign, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Campaigns).where(models.Campaigns.campaign_id==campaign_id))
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign_data.user_id != campaign.user_id:
        user_check = db.execute(select(models.Users).where(models.Users.user_id==campaign_data.user_id))
        user = user_check.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    campaign.campaign_name = campaign_data.campaign_name
    campaign.campaign_details = campaign_data.campaign_details
    campaign.user_id = campaign_data.user_id

    db.commit()
    db.refresh(campaign)
    return campaign

# [API] PATCH ENDPOINT TO UPDATE A CAMPAIGN BY ID
@app.patch(path="/api/campaigns/{campaign_id}", response_model=ResponseCampaign) 
def update_campaign_partial(campaign_id: int, campaign_data: UpdateCampaign, db: Annotated[Session, Depends(get_db)]):

    # Check campaign exists
    result = db.execute(select(models.Campaigns).where(models.Campaigns.campaign_id==campaign_id))
    campaign = result.scalars().first()
    
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found")
    
    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)
    return campaign


# [API] PATCH ENDPOINT TO UPDATE A USER BY THEIR USER_ ID
@app.patch(path="/api/users/{user_id}", response_model=ResponseUser) 
def update_user_partial(user_id: int, user_data: UpdateUser, db: Annotated[Session, Depends(get_db)]):

    # Check user exists
    result = db.execute(select(models.Users).where(models.Users.user_id==user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found")
    
    if user_data.username != None and user_data.username != user.username: # Check if new username doesn't match old username
        user_result = db.execute(select(models.Users).where(models.Users.username==user_data.username)) # Check if new username doesn't match username in DB
        existing_user = user_result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
    if user_data.email != None and user_data.email != user.email: 
        email_result = db.execute(select(models.Users).where(models.Users.email==user_data.email)) 
        existing_email = email_result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")


    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    # OORR
    # if update_data.username is not None:
    #    user.username = update_data.username

    db.commit()
    db.refresh(user)
    return user
            

# --------------------------------------------------------------------------------------------------------
# -------------------------------------------   DELETE ENDPOINTS   ---------------------------------------
# --------------------------------------------------------------------------------------------------------

# [API] DELETE CAMPAIGNS BY ID
@app.delete(
        path="/api/campaigns/{campaign_id}",
        status_code=status.HTTP_204_NO_CONTENT
        )
def delete_campaign(campaign_id: int, db: Annotated[Session, Depends(get_db)]):

    results = db.execute(select(models.Campaigns).where(models.Campaigns.campaign_id==campaign_id))
    campaign = results.scalars().first()

    # Need to add checks to make sure the user making the delete is the author of the campaign

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No campaign found")
    
    db.delete(campaign)
    db.commit()


# [API] DELETE USER BY ID
@app.delete(
        path="/api/users/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT
        )
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):

    results = db.execute(select(models.Users).where(models.Users.user_id==user_id))
    user = results.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found")
    
    db.delete(user)
    db.commit()



# --------------------------------------------------------------------------------------------------------
# -------------------------------   EXCEPTION HANDLING ENDPOINTS   ---------------------------------------
# --------------------------------------------------------------------------------------------------------


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