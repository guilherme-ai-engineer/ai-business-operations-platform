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

def get_customer_orders(
    customer_email: str,
) -> dict:
    db = SessionLocal()

    try:
        orders = db.scalars(
            select(Order)
            .where(
                Order.customer_email == customer_email
            )
            .order_by(Order.id)
        ).all()

        if not orders:
            return {
                "found": False,
                "message": "No orders were found for this customer.",
            }

        return {
            "found": True,
            "orders": [
                {
                    "order_id": order.id,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "estimated_delivery": order.estimated_delivery,
                }
                for order in orders
            ],
        }

    finally:
        db.close()


