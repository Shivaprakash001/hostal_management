from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snacks = "snacks"


class MenuCreate(BaseModel):
    date: datetime
    meal_type: MealType
    items: str  # JSON string or comma-separated items


class MenuUpdate(BaseModel):
    date: Optional[datetime] = None
    meal_type: Optional[MealType] = None
    items: Optional[str] = None


class MenuResponse(BaseModel):
    id: int
    date: datetime
    meal_type: MealType
    items: str

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    student_id: int
    menu_id: int
    date: datetime
    meal_type: MealType
    rating: int  # 1-5 rating
    comment: Optional[str] = None


class FeedbackUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    student_id: int
    menu_id: int
    date: datetime
    meal_type: MealType
    rating: int
    comment: Optional[str] = None
    student_name: Optional[str] = None  # For display purposes

    class Config:
        from_attributes = True


class MenuWithFeedbackResponse(BaseModel):
    id: int
    date: datetime
    meal_type: MealType
    items: str
    feedbacks: List[FeedbackResponse] = []

    class Config:
        from_attributes = True
