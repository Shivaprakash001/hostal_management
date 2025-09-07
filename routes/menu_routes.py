from fastapi import APIRouter, HTTPException, Depends, status, Query
from models.models import User, UserRole
from database.db import Session
from services.menu_services import (
    create_menu, get_menus, get_menu_by_id, update_menu, delete_menu,
    create_feedback, get_feedbacks, update_feedback, delete_feedback,
    get_menu_feedback_stats
)
from schemas.menu import (
    MenuCreate, MenuUpdate, MenuResponse, MenuWithFeedbackResponse,
    FeedbackCreate, FeedbackUpdate, FeedbackResponse
)
from utils.auth import get_current_user, require_role
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/menu", tags=["menu"])

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Menu CRUD endpoints

@router.post("/", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def add_menu(
    menu: MenuCreate,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.chef])),
    db: Session = Depends(get_db)
):
    """Create a new menu item (Admin/Chef only)"""
    return create_menu(menu, db)


@router.get("/", response_model=List[MenuResponse])
def list_menus(
    date: Optional[datetime] = Query(None, description="Filter by date"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type (breakfast, lunch, dinner, snacks)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all menus with optional filtering"""
    return get_menus(db, date, meal_type)


@router.get("/{menu_id}", response_model=MenuWithFeedbackResponse)
def get_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific menu with its feedbacks"""
    return get_menu_by_id(menu_id, db)


@router.put("/{menu_id}", response_model=MenuResponse)
def modify_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.chef])),
    db: Session = Depends(get_db)
):
    """Update a menu item (Admin/Chef only)"""
    return update_menu(menu_id, menu_update, db)


@router.delete("/{menu_id}", response_model=dict)
def remove_menu(
    menu_id: int,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.chef])),
    db: Session = Depends(get_db)
):
    """Delete a menu item (Admin/Chef only)"""
    return delete_menu(menu_id, db)


# Feedback CRUD endpoints

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def add_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create feedback for a menu (All authenticated users)"""
    # If student, ensure they can only give feedback for themselves
    if current_user.role == UserRole.student and current_user.student_id != feedback.student_id:
        raise HTTPException(status_code=403, detail="Students can only submit feedback for themselves")

    return create_feedback(feedback, db)


@router.get("/feedback/", response_model=List[FeedbackResponse])
def list_feedbacks(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    menu_id: Optional[int] = Query(None, description="Filter by menu ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all feedbacks with optional filtering"""
    # If student, only show their own feedback
    if current_user.role == UserRole.student and current_user.student_id:
        student_id = current_user.student_id

    return get_feedbacks(db, student_id, menu_id)


@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
def modify_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update feedback (Users can only update their own feedback)"""
    # Get the feedback to check ownership
    from models.models import Feedback
    feedback = db.query(Feedback).filter_by(id=feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Check permissions
    if current_user.role not in [UserRole.admin, UserRole.chef]:
        if current_user.student_id != feedback.student_id:
            raise HTTPException(status_code=403, detail="You can only update your own feedback")

    return update_feedback(feedback_id, feedback_update, db)


@router.delete("/feedback/{feedback_id}", response_model=dict)
def remove_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete feedback (Users can only delete their own feedback, admins can delete any)"""
    # Get the feedback to check ownership
    from models.models import Feedback
    feedback = db.query(Feedback).filter_by(id=feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Check permissions
    if current_user.role not in [UserRole.admin, UserRole.chef]:
        if current_user.student_id != feedback.student_id:
            raise HTTPException(status_code=403, detail="You can only delete your own feedback")

    return delete_feedback(feedback_id, db)


# Analytics endpoints

@router.get("/{menu_id}/stats", response_model=dict)
def get_menu_stats(
    menu_id: int,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.chef])),
    db: Session = Depends(get_db)
):
    """Get feedback statistics for a menu (Admin/Chef only)"""
    return get_menu_feedback_stats(menu_id, db)


# Bulk operations

@router.post("/bulk", response_model=List[MenuResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_menus(
    menus: List[MenuCreate],
    current_user: User = Depends(require_role([UserRole.admin, UserRole.chef])),
    db: Session = Depends(get_db)
):
    """Create multiple menu items at once (Admin/Chef only)"""
    created_menus = []
    for menu_data in menus:
        try:
            menu = create_menu(menu_data, db)
            created_menus.append(menu)
        except Exception as e:
            # Continue with other menus if one fails
            continue

    return [MenuResponse.from_orm(menu) for menu in created_menus]


@router.get("/today/", response_model=List[MenuResponse])
def get_today_menus(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's menu items"""
    today = datetime.now().date()
    return get_menus(db, date=today)


@router.get("/date/{date_str}", response_model=List[MenuResponse])
def get_menus_by_date(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get menus for a specific date (YYYY-MM-DD format)"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return get_menus(db, date=date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
