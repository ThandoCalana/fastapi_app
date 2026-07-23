from datetime import datetime, timedelta
from random import randint
from typing import Annotated
from contextlib import asynccontextmanager  # Will be used as decorator for lifespan

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Request, status, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # For eager loading relationships in models

from database import get_db, engine, Base
import models
from routers import users, campaigns

# py -c "import secrets; print(secrets.token_hex(32))" to generate a secret in terminal


@asynccontextmanager
async def lifespan(_app: FastAPI):

    # At startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    # At Shtudown
    await engine.dispose()


# Looks at all models inheriting from Base and creates them if they don't exist

app = FastAPI(lifespan=lifespan)

# Mounting static folder to the app. Now, anything inside static folder is accessible
# Inputs => file path, instance of StaticFiles class using the 'static' folder, name we can use to ref in templates
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

# Tells templating framework to look for our templates in the 'templates' dir/ folder
templates = Jinja2Templates(directory="templates")

app.include_router(router=users.router, prefix="/api/users", tags=["users"])
app.include_router(router=campaigns.router, prefix="/api/campaigns", tags=["campaigns"])


# Another way to add an API route
# app.add_api_route(
#     methods=["GET"],
#     endpoint=get_campaigns
# )

# datetime.now().strftime('%Y-%m-%dT%H:%M')
now = datetime.now()
due = now + timedelta(days=randint(1, 10))


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
    name="home",  # name so we know which unique route to access. Affects URL path user gets directed to
    include_in_schema=False,  # Exclude from API documentation
)
@app.get(
    path="/campaigns", name="campaigns", include_in_schema=False
)  # Not useful for API consumption/ dev. THESE ARE ONLY HTML ENDPOINTS NOT API FUNCTIONALITY
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    query = await db.execute(
        select(models.Campaigns).options(selectinload(models.Campaigns.author)).order_by(models.Campaigns.created_at.desc())
    )
    campaigns = query.scalars().all()

    # Pass campaigns dict list to be used in/on the actual html template file
    return templates.TemplateResponse(
        request, "home.html", {"campaigns": campaigns, "title": "Home"}
    )


# [HTML] Fetch current user's campaigns
@app.get(
    path="/users/{user_id}/campaigns", name="user_campaigns", include_in_schema=False
)
async def get_user_campaigns(
    request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    user_check = await db.execute(
        select(models.Users).where(models.Users.user_id == user_id)
    )
    user = user_check.scalars().first()  # selects one or none, Returns None
    # users = query.scalar_one() raises an error if nothing is found

    if user:
        result = await db.execute(
            select(models.Campaigns)
            .options(selectinload(models.Campaigns.author))
            .where(models.Campaigns.user_id == user_id)
            .order_by(models.Campaigns.created_at.desc())
        )       
        campaigns = result.scalars().all()

        if campaigns:
            return templates.TemplateResponse(
                request=request,
                name="user_campaigns.html",
                context={"campaigns": campaigns, "user": user},
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No campaigns found"
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# [HTML] GET CAMPAIGNS BY ID
@app.get(
    path="/campaigns/{campaign_id}",
    name="campaign",
    description="Get a campaign by its ID",
    include_in_schema=False,
)
async def campaign_page(
    request: Request, campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):

    results = await db.execute(
        select(models.Campaigns)
        .options(selectinload(models.Campaigns.author))
        .where(models.Campaigns.campaign_id == campaign_id)
    )
    campaign = results.scalars().first()

    if campaign:
        title = campaign.campaign_name
        return templates.TemplateResponse(
            request, "campaign.html", {"campaign": campaign, "title": title}
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No campaign Found"
    )

@app.get(
    path="/register",
    name="register_page",
    include_in_schema=False,
)
async def register(request: Request):
    return templates.TemplateResponse(
        request, "register.html", {"title": "Register"}
    )

@app.get(
    path="/login",
    name="login_page",
    include_in_schema=False,
)
async def login(request: Request):
    return templates.TemplateResponse(
        request, "login.html", {"title": "Login"}
    )

# --------------------------------------------------------------------------------------------------------
# -------------------------------   EXCEPTION HANDLING ENDPOINTS   ---------------------------------------
# --------------------------------------------------------------------------------------------------------


# Using Startlette Exception Handler to catch 'all' HTTP excpetions over and above fastapi's
@app.exception_handler(StarletteHTTPException)
async def exception_handler(request: Request, exception: StarletteHTTPException):

    if request.url.path.startswith("/api/"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "Error occurred. Please check your request and try again"
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):

    if request.url.path.startswith("/api/"):
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid Response. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
