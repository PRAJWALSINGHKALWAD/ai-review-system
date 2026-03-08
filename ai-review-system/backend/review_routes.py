from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import ai_service
import database
import models
import schemas

router = APIRouter()


@router.post("/review", response_model=schemas.ReviewCreateResponse)
def create_review(review_in: schemas.ReviewCreate, db: Session = Depends(database.get_db)):
    review = models.Review(
        review_text=review_in.review_text,
        tone=review_in.tone,
        status="pending",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return schemas.ReviewCreateResponse(review_id=review.id)


@router.post("/generate-response/{review_id}", response_model=schemas.GenerateResponseOutput)
def generate_response(review_id: int, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    latest_response = (
        db.query(models.Response)
        .filter(models.Response.review_id == review_id)
        .order_by(models.Response.version.desc())
        .first()
    )
    next_version = 1 if latest_response is None else latest_response.version + 1

    response_text = ai_service.generate_response(review.review_text, review.tone)

    response_row = models.Response(
        review_id=review.id,
        response_text=response_text,
        revision_notes=None,
        version=next_version,
    )
    review.status = "pending"
    db.add(response_row)
    db.add(review)
    db.commit()
    db.refresh(response_row)

    return schemas.GenerateResponseOutput(
        review_id=review.id,
        response_id=response_row.id,
        version=response_row.version,
        response_text=response_row.response_text,
    )


@router.post("/approve-response", response_model=schemas.StatusResponse)
def approve_response(payload: schemas.ApproveResponseInput, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == payload.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    latest_response = (
        db.query(models.Response)
        .filter(models.Response.review_id == review.id)
        .order_by(models.Response.version.desc())
        .first()
    )
    if not latest_response:
        raise HTTPException(status_code=400, detail="No generated response exists for this review")

    review.status = "approved"
    db.add(review)
    db.commit()
    db.refresh(review)

    return schemas.StatusResponse(review_id=review.id, status=review.status)


@router.post("/request-revision", response_model=schemas.GenerateResponseOutput)
def request_revision(payload: schemas.RevisionRequestInput, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == payload.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    latest_response = (
        db.query(models.Response)
        .filter(models.Response.review_id == review.id)
        .order_by(models.Response.version.desc())
        .first()
    )
    if not latest_response:
        raise HTTPException(status_code=400, detail="No generated response found to revise")

    revised_text = ai_service.revise_response(
        review=review.review_text,
        previous_response=latest_response.response_text,
        notes=payload.notes,
        tone=review.tone,
    )

    revised_row = models.Response(
        review_id=review.id,
        response_text=revised_text,
        revision_notes=payload.notes,
        version=latest_response.version + 1,
    )

    review.status = "revision_requested"
    db.add(revised_row)
    db.add(review)
    db.commit()
    db.refresh(revised_row)

    return schemas.GenerateResponseOutput(
        review_id=review.id,
        response_id=revised_row.id,
        version=revised_row.version,
        response_text=revised_row.response_text,
    )
