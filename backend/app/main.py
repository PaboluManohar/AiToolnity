import hmac
import hashlib
import json
import logging
import math
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from urllib.parse import urlencode

import httpx
from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.catalogue import (
    get_catalogue,
    get_tool,
    list_categories,
    list_items,
    list_subcategories,
)
from app.database import Base, engine, get_db
from app.models import AISettings, Execution, ExecutionAttempt, User
from app.request_guard import RequestGuard
from app.schemas import (
    ExecutionRequest,
    ExecutionResponse,
    RefinementRequest,
    SettingsResponse,
    SettingsUpdate,
    UserResponse,
)
from app.security import (
    create_access_token,
    decrypt_api_key,
    encrypt_api_key,
    get_current_user,
    create_oauth_values,
    secure_cookie,
    session_cookie_name,
    validate_security_configuration,
)
from app.services.openrouter import OpenRouterError, generate


logger = logging.getLogger("aitoolnity.api")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_catalogue()
    validate_security_configuration()
    migration_config = Config(str(os.path.join(os.path.dirname(__file__), "..", "alembic.ini")))
    migration_config.set_main_option(
        "sqlalchemy.url",
        engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    command.upgrade(migration_config, "head")
    yield


production = os.getenv("APP_ENV", "development") == "production"
app = FastAPI(
    title="AIToolnity API",
    version="1.0.0",
    lifespan=lifespan,
    debug=False,
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)
app.add_middleware(RequestGuard, allowed_origins=allowed_origins)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, error: RequestValidationError
) -> JSONResponse:
    errors = [
        {
            "location": [str(part) for part in item.get("loc", ())],
            "message": item.get("msg", "Invalid request."),
            "type": item.get("type", "validation_error"),
        }
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, __: SQLAlchemyError) -> JSONResponse:
    logger.warning("Database request failed.")
    return JSONResponse(
        status_code=503,
        content={"detail": "A database operation failed. Try again shortly."},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, error: StarletteHTTPException) -> JSONResponse:
    detail = error.detail
    if not isinstance(detail, (str, list, dict)):
        detail = "The request could not be completed."
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": detail},
        headers=error.headers,
    )


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok"}


@app.get("/api/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/catalogue/categories")
def categories() -> list[dict[str, str]]:
    return list_categories()


@app.get("/api/catalogue/categories/{category_id}/subcategories")
def subcategories(category_id: str) -> list[dict[str, str]]:
    result = list_subcategories(category_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    return result


@app.get(
    "/api/catalogue/categories/{category_id}/subcategories/{subcategory_id}/items"
)
def items(category_id: str, subcategory_id: str) -> list[dict[str, Any]]:
    result = list_items(category_id, subcategory_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Subcategory not found.")
    return result


@app.get("/api/catalogue/tools/{tool_id}")
def tool_configuration(tool_id: str) -> dict[str, Any]:
    tool = get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found or disabled.")
    return tool


@app.get("/api/auth/google/start")
def google_login_start() -> RedirectResponse:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id or not os.getenv("GOOGLE_CLIENT_SECRET"):
        raise HTTPException(
            status_code=503, detail="Google Login is not configured for this application."
        )
    state, verifier, challenge, nonce = create_oauth_values()
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback"
    )
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    redirect = RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    )
    redirect.set_cookie(
        "aitoolnity_oauth_state",
        state,
        httponly=True,
        secure=secure_cookie(),
        samesite="lax",
        max_age=300,
    )
    redirect.set_cookie(
        "aitoolnity_oauth_verifier",
        verifier,
        httponly=True,
        secure=secure_cookie(),
        samesite="lax",
        max_age=300,
    )
    redirect.set_cookie(
        "aitoolnity_oauth_nonce",
        nonce,
        httponly=True,
        secure=secure_cookie(),
        samesite="lax",
        max_age=300,
    )
    return redirect


@app.get("/api/auth/google/callback")
async def google_login_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    if error:
        response = RedirectResponse(f"{frontend_url}/?auth_error=google_login_cancelled")
        response.delete_cookie("aitoolnity_oauth_state", path="/")
        response.delete_cookie("aitoolnity_oauth_verifier", path="/")
        response.delete_cookie("aitoolnity_oauth_nonce", path="/")
        return response
    expected_state = request.cookies.get("aitoolnity_oauth_state")
    verifier = request.cookies.get("aitoolnity_oauth_verifier")
    nonce = request.cookies.get("aitoolnity_oauth_nonce")
    if (
        not code
        or not state
        or not expected_state
        or not verifier
        or not nonce
        or not hmac.compare_digest(state, expected_state)
    ):
        raise HTTPException(status_code=400, detail="Google Login state validation failed.")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Google Login is not configured.")

    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback"
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": verifier,
                },
            )
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502, detail="Could not connect to Google. Try again."
        ) from error
    if token_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Google Login could not be completed.")
    try:
        token_data: Any = token_response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=502, detail="Google returned an invalid token response."
        ) from error
    id_token_value = token_data.get("id_token")
    if not isinstance(id_token_value, str):
        raise HTTPException(status_code=401, detail="Google did not return an identity token.")
    try:
        claims = id_token.verify_oauth2_token(
            id_token_value, GoogleRequest(), audience=client_id
        )
    except (ValueError, JWTError) as error:
        raise HTTPException(status_code=401, detail="Google identity validation failed.") from error
    token_nonce = claims.get("nonce")
    if not isinstance(token_nonce, str) or not hmac.compare_digest(token_nonce, nonce):
        raise HTTPException(status_code=401, detail="Google identity validation failed.")

    google_sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")
    if not isinstance(google_sub, str) or not isinstance(email, str) or not isinstance(name, str):
        raise HTTPException(status_code=401, detail="Google did not return a complete profile.")
    if claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Your Google email address is not verified.")

    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            raise HTTPException(
                status_code=409, detail="This email is already linked to another account."
            )
        user = User(google_sub=google_sub, email=email, name=name)
        db.add(user)
        db.flush()
        db.add(AISettings(user_id=user.id, model=get_catalogue().default_model))
        db.commit()
        db.refresh(user)
    response = RedirectResponse(f"{frontend_url}/")
    response.delete_cookie("aitoolnity_oauth_state", path="/")
    response.delete_cookie("aitoolnity_oauth_verifier", path="/")
    response.delete_cookie("aitoolnity_oauth_nonce", path="/")
    response.set_cookie(
        session_cookie_name(),
        create_access_token(user.id),
        httponly=True,
        secure=secure_cookie(),
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return response


@app.get("/api/auth/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)


@app.get("/api/auth/status", response_model=UserResponse | None)
def auth_status(request: Request, db: Session = Depends(get_db)) -> UserResponse | None:
    token = request.cookies.get(session_cookie_name())
    if not token:
        return None
    secret = os.getenv("APP_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        return None
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return None
    return UserResponse(id=user.id, email=user.email, name=user.name)


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(
        session_cookie_name(),
        path="/",
        secure=secure_cookie(),
        httponly=True,
        samesite="lax",
    )
    return {"status": "signed_out"}


def _user_settings(db: Session, user_id: int) -> AISettings:
    settings = db.scalar(select(AISettings).where(AISettings.user_id == user_id))
    if settings is None:
        settings = AISettings(user_id=user_id, model=get_catalogue().default_model)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _response_settings(settings: AISettings) -> SettingsResponse:
    return SettingsResponse(
        model=settings.model,
        has_api_key=settings.encrypted_api_key is not None,
    )


@app.get("/api/settings", response_model=SettingsResponse)
def read_settings(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> SettingsResponse:
    return _response_settings(_user_settings(db, user.id))


@app.put("/api/settings", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsResponse:
    settings = _user_settings(db, user.id)
    settings.model = body.model
    if body.api_key is not None:
        settings.encrypted_api_key = encrypt_api_key(body.api_key)
    db.commit()
    db.refresh(settings)
    return _response_settings(settings)


@app.delete("/api/settings/api-key", response_model=SettingsResponse)
def remove_api_key(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsResponse:
    settings = _user_settings(db, user.id)
    settings.encrypted_api_key = None
    db.commit()
    db.refresh(settings)
    return _response_settings(settings)


async def _api_key_for_user(db: Session, user: User) -> tuple[str, str]:
    settings = _user_settings(db, user.id)
    if settings.encrypted_api_key:
        return decrypt_api_key(settings.encrypted_api_key), settings.model
    raise HTTPException(
        status_code=400,
        detail="Add your OpenRouter API key in AI settings before generating a result.",
    )


async def _call_provider(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    try:
        return await generate(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except OpenRouterError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error


def _validate_inputs(tool: dict[str, Any], inputs: dict[str, Any]) -> str:
    fields = tool["input_schema"]["fields"]
    allowed = {field["name"] for field in fields}
    unexpected = set(inputs) - allowed
    if unexpected:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown input field: {', '.join(sorted(unexpected))}.",
        )
    lines: list[str] = []
    for field in fields:
        value = inputs.get(field["name"])
        if value is None or value == "" or (isinstance(value, str) and not value.strip()):
            if field["required"]:
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} is required."
                )
            continue
        if field["type"] == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} must be a number."
                )
            if field["min_value"] is not None and value < field["min_value"]:
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} is below its minimum."
                )
            if field["max_value"] is not None and value > field["max_value"]:
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} exceeds its maximum."
                )
            if not math.isfinite(value):
                raise HTTPException(
                    status_code=422,
                    detail=f"{field['label']} must be a finite number.",
                )
        elif not isinstance(value, str):
            raise HTTPException(
                status_code=422, detail=f"{field['label']} must be text."
            )
        elif field["type"] == "select" and value not in field["options"]:
            raise HTTPException(
                status_code=422, detail=f"Choose a valid option for {field['label']}."
            )
        elif field["type"] == "email" and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", value
        ):
            raise HTTPException(
                status_code=422, detail=f"{field['label']} must be a valid email address."
            )
        elif field["type"] == "url" and not _valid_url(value):
            raise HTTPException(
                status_code=422, detail=f"{field['label']} must start with http:// or https://."
            )
        elif field["type"] != "number":
            if field["min_length"] is not None and len(value) < field["min_length"]:
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} is too short."
                )
            maximum_length = field["max_length"] or 20_000
            if len(value) > maximum_length:
                raise HTTPException(
                    status_code=422, detail=f"{field['label']} is too long."
                )
        lines.append(f"{field['label']}:\n{value}")
    return "\n\n".join(lines)


def _valid_url(value: str) -> bool:
    from urllib.parse import urlsplit

    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _tone(tool: dict[str, Any], tone_id: str) -> dict[str, str]:
    tone = next((item for item in tool["tones"] if item["id"] == tone_id), None)
    if tone is None:
        raise HTTPException(status_code=422, detail="Choose a supported tone.")
    return tone


def _execution_response(execution: Execution) -> ExecutionResponse:
    return ExecutionResponse(
        id=execution.id,
        tool_id=execution.tool_id,
        input_data=execution.input_data,
        result=execution.result,
        model=execution.model,
        tone=execution.tone,
        created_at=execution.created_at or datetime.now(timezone.utc),
    )


async def _save_execution(
    *,
    db: Session,
    user: User,
    tool: dict[str, Any],
    input_data: dict[str, Any],
    tone_id: str,
    parent_id: int | None = None,
    refinement: str | None = None,
    previous_result: str | None = None,
    request_key: str,
) -> ExecutionResponse:
    user_prompt = _validate_inputs(tool, input_data)
    selected_tone = _tone(tool, tone_id)
    if refinement is not None:
        user_prompt += (
            "\n\nPrevious result:\n"
            + (previous_result or "")
            + "\n\nRefinement instructions:\n"
            + refinement
        )
    request_hash = hashlib.sha256(
        json.dumps(
            {
                "tool_id": tool["id"],
                "inputs": input_data,
                "tone": tone_id,
                "parent_id": parent_id,
                "refinement": refinement,
                "previous_result": previous_result,
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    attempt = ExecutionAttempt(
        user_id=user.id,
        request_key=request_key,
        request_hash=request_hash,
        status="pending",
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_attempt = db.scalar(
            select(ExecutionAttempt).where(
                ExecutionAttempt.user_id == user.id,
                ExecutionAttempt.request_key == request_key,
            )
        )
        if (
            existing_attempt
            and existing_attempt.request_hash != request_hash
        ):
            raise HTTPException(
                status_code=409,
                detail="This request key has already been used for different input.",
            )
        if (
            existing_attempt
            and existing_attempt.status == "complete"
            and existing_attempt.execution_id
        ):
            existing_execution = db.get(Execution, existing_attempt.execution_id)
            if existing_execution is not None:
                return _execution_response(existing_execution)
        raise HTTPException(
            status_code=409,
            detail="This request is already being processed. Wait before retrying.",
        )

    try:
        api_key, model = await _api_key_for_user(db, user)
        result = await _call_provider(
            api_key=api_key,
            model=model,
            system_prompt=(
                f"{tool['system_prompt']}\n\n"
                f"Requested tone: {selected_tone['name']}. {selected_tone['instructions']}"
            ),
            user_prompt=user_prompt,
        )
        execution = Execution(
            user_id=user.id,
            parent_id=parent_id,
            tool_id=tool["id"],
            input_data=input_data,
            result=result,
            model=model,
            tone=tone_id,
        )
        db.add(execution)
        db.flush()
        attempt.status = "complete"
        attempt.execution_id = execution.id
        db.commit()
        db.refresh(execution)
        return _execution_response(execution)
    except HTTPException:
        db.rollback()
        _discard_attempt(db, user.id, request_key)
        raise
    except SQLAlchemyError as error:
        db.rollback()
        _discard_attempt(db, user.id, request_key)
        logger.warning("Could not persist an AI execution.")
        raise HTTPException(
            status_code=503,
            detail="The result could not be saved. Check your history before retrying.",
        ) from error


def _discard_attempt(db: Session, user_id: int, request_key: str) -> None:
    attempt = db.scalar(
        select(ExecutionAttempt).where(
            ExecutionAttempt.user_id == user_id,
            ExecutionAttempt.request_key == request_key,
        )
    )
    if attempt is not None:
        db.delete(attempt)
        db.commit()


@app.post("/api/executions", response_model=ExecutionResponse)
async def execute_tool(
    body: ExecutionRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=16, max_length=64
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExecutionResponse:
    tool = get_tool(body.tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found or disabled.")
    return await _save_execution(
        db=db,
        user=user,
        tool=tool,
        input_data=body.inputs,
        tone_id=body.tone,
        request_key=idempotency_key,
    )


def _owned_execution(db: Session, user_id: int, execution_id: int) -> Execution:
    execution = db.scalar(
        select(Execution).where(
            Execution.id == execution_id, Execution.user_id == user_id
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Saved result not found.")
    return execution


@app.post("/api/executions/{execution_id}/regenerate", response_model=ExecutionResponse)
async def regenerate_result(
    execution_id: int,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=16, max_length=64
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExecutionResponse:
    original = _owned_execution(db, user.id, execution_id)
    tool = get_tool(original.tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="The original tool is no longer available.")
    return await _save_execution(
        db=db,
        user=user,
        tool=tool,
        input_data=original.input_data,
        tone_id=original.tone,
        parent_id=original.id,
        request_key=idempotency_key,
    )


@app.post("/api/executions/{execution_id}/refine", response_model=ExecutionResponse)
async def refine_result(
    execution_id: int,
    body: RefinementRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=16, max_length=64
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExecutionResponse:
    original = _owned_execution(db, user.id, execution_id)
    tool = get_tool(original.tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="The original tool is no longer available.")
    if not body.instructions or not body.instructions.strip():
        raise HTTPException(status_code=422, detail="Add refinement instructions.")
    tone_id = body.tone or original.tone
    return await _save_execution(
        db=db,
        user=user,
        tool=tool,
        input_data=original.input_data,
        tone_id=tone_id,
        parent_id=original.id,
        refinement=body.instructions.strip(),
        previous_result=original.result,
        request_key=idempotency_key,
    )


@app.get("/api/history", response_model=list[ExecutionResponse])
def execution_history(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExecutionResponse]:
    executions = db.scalars(
        select(Execution)
        .where(Execution.user_id == user.id)
        .order_by(Execution.created_at.desc(), Execution.id.desc())
        .limit(limit)
    ).all()
    return [_execution_response(item) for item in executions]


@app.post("/api/settings/test")
async def test_openrouter(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    api_key, model = await _api_key_for_user(db, user)
    result = await _call_provider(
        api_key=api_key,
        model=model,
        system_prompt="Reply with the single word ready.",
        user_prompt="Confirm that this model can respond.",
    )
    return {"status": "connected", "response": result, "model": model}
