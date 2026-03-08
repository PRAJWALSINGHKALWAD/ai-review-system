from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import ai_service
import database
import models
import schemas

router = APIRouter()


@router.get("/responses/{review_id}", response_model=list[schemas.ResponseVersionOutput])
def list_response_versions(review_id: int, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    rows = (
        db.query(models.Response)
        .filter(models.Response.review_id == review_id)
        .order_by(models.Response.version.asc())
        .all()
    )

    return [
        schemas.ResponseVersionOutput(
            response_id=row.id,
            version=row.version,
            response_text=row.response_text,
            revision_notes=row.revision_notes,
        )
        for row in rows
    ]


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

    # Initial generation should create version 1 once.
    # Repeated calls return the latest generated response for this review.
    if latest_response is not None:
        return schemas.GenerateResponseOutput(
            review_id=review.id,
            response_id=latest_response.id,
            version=latest_response.version,
            response_text=latest_response.response_text,
        )

    generated = ai_service.generate_structured_response(
        review=review.review_text,
        tone=review.tone,
        next_version=1,
        previous_versions=[],
        owner_improvement="",
    )

    response_row = models.Response(
        review_id=review.id,
        response_text=generated["business_post"],
        revision_notes=None,
        version=1,
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

    history_rows = (
        db.query(models.Response)
        .filter(models.Response.review_id == review.id)
        .order_by(models.Response.version.asc())
        .all()
    )
    previous_versions = [
        {
            "version": row.version,
            "response_text": row.response_text,
            "context": row.revision_notes,
        }
        for row in history_rows
    ]

    revised = ai_service.generate_structured_response(
        review=review.review_text,
        tone=review.tone,
        next_version=latest_response.version + 1,
        previous_versions=previous_versions,
        owner_improvement=payload.notes,
    )

    revised_row = models.Response(
        review_id=review.id,
        response_text=revised["business_post"],
        revision_notes=payload.notes,
        version=revised["version"],
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
