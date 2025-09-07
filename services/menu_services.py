from models.models import Menu, Feedback, Student
from database.db import Session
from typing import List, Optional
from fastapi import HTTPException
from schemas.menu import MenuCreate, MenuUpdate, MenuResponse, FeedbackCreate, FeedbackUpdate, FeedbackResponse, MenuWithFeedbackResponse
from datetime import datetime


def create_menu(menu_data: MenuCreate, db: Session) -> Menu:
    try:
        # Check if menu already exists for this date and meal type
        existing_menu = db.query(Menu).filter_by(
            date=menu_data.date,
            meal_type=menu_data.meal_type
        ).first()

        if existing_menu:
            raise HTTPException(
                status_code=400,
                detail=f"Menu already exists for {menu_data.date} - {menu_data.meal_type}"
            )

        menu = Menu(
            date=menu_data.date,
            meal_type=menu_data.meal_type,
            items=menu_data.items
        )

        db.add(menu)
        db.commit()
        db.refresh(menu)
        return menu

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_menus(db: Session, date: Optional[datetime] = None, meal_type: Optional[str] = None) -> List[MenuResponse]:
    try:
        query = db.query(Menu)

        if date:
            query = query.filter_by(date=date)
        if meal_type:
            query = query.filter_by(meal_type=meal_type)

        menus = query.order_by(Menu.date.desc(), Menu.meal_type).all()
        return [MenuResponse.from_orm(menu) for menu in menus]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_menu_by_id(menu_id: int, db: Session) -> MenuWithFeedbackResponse:
    try:
        menu = db.query(Menu).filter_by(id=menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {menu_id} not found")

        # Get feedbacks with student names
        feedbacks = []
        for feedback in menu.feedbacks:
            feedback_data = FeedbackResponse.from_orm(feedback)
            feedback_data.student_name = feedback.student.name
            feedbacks.append(feedback_data)

        return MenuWithFeedbackResponse(
            id=menu.id,
            date=menu.date,
            meal_type=menu.meal_type,
            items=menu.items,
            feedbacks=feedbacks
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_menu(menu_id: int, menu_update: MenuUpdate, db: Session) -> MenuResponse:
    try:
        menu = db.query(Menu).filter_by(id=menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {menu_id} not found")

        if menu_update.date is not None:
            menu.date = menu_update.date
        if menu_update.meal_type is not None:
            menu.meal_type = menu_update.meal_type
        if menu_update.items is not None:
            menu.items = menu_update.items

        db.commit()
        db.refresh(menu)
        return MenuResponse.from_orm(menu)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def delete_menu(menu_id: int, db: Session):
    try:
        menu = db.query(Menu).filter_by(id=menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {menu_id} not found")

        db.delete(menu)
        db.commit()
        return {"message": "Menu deleted successfully", "deleted_menu_id": menu_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def create_feedback(feedback_data: FeedbackCreate, db: Session) -> Feedback:
    try:
        # Check if student exists
        student = db.query(Student).filter_by(id=feedback_data.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student with ID {feedback_data.student_id} not found")

        # Check if menu exists
        menu = db.query(Menu).filter_by(id=feedback_data.menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {feedback_data.menu_id} not found")

        # Check if feedback already exists for this student and menu
        existing_feedback = db.query(Feedback).filter_by(
            student_id=feedback_data.student_id,
            menu_id=feedback_data.menu_id
        ).first()

        if existing_feedback:
            raise HTTPException(
                status_code=400,
                detail=f"Feedback already exists for this student and menu"
            )

        # Validate rating (1-5)
        if not (1 <= feedback_data.rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        feedback = Feedback(
            student_id=feedback_data.student_id,
            menu_id=feedback_data.menu_id,
            date=feedback_data.date,
            meal_type=feedback_data.meal_type,
            rating=feedback_data.rating,
            comment=feedback_data.comment
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_feedbacks(db: Session, student_id: Optional[int] = None, menu_id: Optional[int] = None) -> List[FeedbackResponse]:
    try:
        query = db.query(Feedback)

        if student_id:
            query = query.filter_by(student_id=student_id)
        if menu_id:
            query = query.filter_by(menu_id=menu_id)

        feedbacks = query.order_by(Feedback.date.desc()).all()

        # Add student names to responses
        result = []
        for feedback in feedbacks:
            feedback_data = FeedbackResponse.from_orm(feedback)
            feedback_data.student_name = feedback.student.name
            result.append(feedback_data)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_feedback(feedback_id: int, feedback_update: FeedbackUpdate, db: Session) -> FeedbackResponse:
    try:
        feedback = db.query(Feedback).filter_by(id=feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail=f"Feedback with ID {feedback_id} not found")

        if feedback_update.rating is not None:
            if not (1 <= feedback_update.rating <= 5):
                raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
            feedback.rating = feedback_update.rating

        if feedback_update.comment is not None:
            feedback.comment = feedback_update.comment

        db.commit()
        db.refresh(feedback)

        feedback_data = FeedbackResponse.from_orm(feedback)
        feedback_data.student_name = feedback.student.name
        return feedback_data

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def delete_feedback(feedback_id: int, db: Session):
    try:
        feedback = db.query(Feedback).filter_by(id=feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail=f"Feedback with ID {feedback_id} not found")

        db.delete(feedback)
        db.commit()
        return {"message": "Feedback deleted successfully", "deleted_feedback_id": feedback_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_menu_feedback_stats(menu_id: int, db: Session):
    try:
        menu = db.query(Menu).filter_by(id=menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {menu_id} not found")

        feedbacks = db.query(Feedback).filter_by(menu_id=menu_id).all()

        if not feedbacks:
            return {
                "menu_id": menu_id,
                "total_feedbacks": 0,
                "average_rating": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        total_feedbacks = len(feedbacks)
        average_rating = sum(f.rating for f in feedbacks) / total_feedbacks

        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for feedback in feedbacks:
            rating_distribution[feedback.rating] += 1

        return {
            "menu_id": menu_id,
            "total_feedbacks": total_feedbacks,
            "average_rating": round(average_rating, 2),
            "rating_distribution": rating_distribution
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
