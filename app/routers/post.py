from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models_db, schemas, oauth2
from typing import List, Optional
from sqlalchemy.orm import Session
from app.stng import get_db
from sqlalchemy import func
from icecream import ic

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

# @router.get("/", response_model=List[schemas.Post])
@router.get("/", response_model=List[schemas.PostOut])
def get_all_posts(db: Session = Depends(get_db), 
                  current_user: int = Depends(oauth2.get_current_user), 
                  limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    ic(limit)
    ic(search)

    posts = db.query(models_db.Post, func.count(models_db.Vote.post_id).label("likes")).join(
        models_db.Vote, models_db.Vote.post_id == models_db.Post.id, isouter=True
                                            ).group_by(models_db.Post.id).filter(
                                                models_db.Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # Create a new post using SQLAlchemy ORM
    new_post = models_db.Post(
        title=post.title,
        content=post.content,
        published=post.published,
        owner_id=current_user.id
    )

    db.add(new_post)
    db.commit()

    return new_post

@router.get("/latest", response_model=schemas.PostOut)
def get_latest_post(db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    post = db.query(models_db.Post, func.count(models_db.Vote.post_id).label("likes")).order_by(models_db.Post.created_at.desc()).join(
        models_db.Vote, models_db.Vote.post_id == models_db.Post.id, isouter=True
                                            ).group_by(models_db.Post.id).first()
    return post

@router.get("/{id}", response_model=schemas.PostOut)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models_db.Post, func.count(models_db.Vote.post_id).label("likes")).join(
        models_db.Vote, models_db.Vote.post_id == models_db.Post.id, isouter=True
                                            ).group_by(models_db.Post.id).filter(models_db.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                             detail=f"post with id: {id} was not found")
    return post

@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    post = db.query(models_db.Post).filter(models_db.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.Post)
def update_post(
    id: int, 
    post: schemas.PostCreate, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(oauth2.get_current_user)
):
    existing_post = db.query(models_db.Post).filter(models_db.Post.id == id).first()
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Post with id: {id} was not found")
    
    if existing_post.owner_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Not authorized to perform the requested action")

    existing_post.title = post.title
    existing_post.content = post.content
    existing_post.published = post.published

    db.commit()
    db.refresh(existing_post)

    return existing_post