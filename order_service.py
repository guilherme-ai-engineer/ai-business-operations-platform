from sqlalchemy import select

from database import SessionLocal
from models import Order


def get_order_status(order_id: int) -> dict:
    db = SessionLocal()

    try:
        order = db.scalar(
            select(Order).where(
                Order.id == order_id
            )
        )

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found.",
            }

        return {
            "found": True,
            "order_id": order.id,
            "customer_email": order.customer_email,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "estimated_delivery": order.estimated_delivery,
        }

    finally:
        db.close()


if __name__ == "__main__":
    result = get_order_status(9999)

    print(result)