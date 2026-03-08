from typing import Literal

from pydantic import BaseModel

ReviewStatus = Literal["pending", "revision_requested", "approved"]


class ReviewCreate(BaseModel):
    review_text: str
    tone: str


class ReviewCreateResponse(BaseModel):
    review_id: int


class GenerateResponseOutput(BaseModel):
    review_id: int
    response_id: int
    version: int
    response_text: str


class ApproveResponseInput(BaseModel):
    review_id: int


class StatusResponse(BaseModel):
    review_id: int
    status: ReviewStatus


class RevisionRequestInput(BaseModel):
    review_id: int
    notes: str
