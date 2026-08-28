from sqlalchemy import select

from database import SessionLocal
from models import Order


def get_order_status(
    order_id: int,
    customer_email: str,
) -> dict:
    db = SessionLocal()

    try:
        order = db.scalar(
            select(Order).where(
                Order.id == order_id,
                Order.customer_email == customer_email,
            )
        )

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found for this customer.",
            }

        return {
            "found": True,
            "order_id": order.id,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "estimated_delivery": order.estimated_delivery,
        }

    finally:
        db.close()