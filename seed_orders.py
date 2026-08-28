from sqlalchemy import select

from database import SessionLocal
from models import Order


def seed_orders():
    orders = [
        Order(
            id=1042,
            customer_email="john@example.com",
            status="in_transit",
            total_amount=349.90,
            estimated_delivery="2026-08-31",
        ),
        Order(
            id=1043,
            customer_email="emma@example.com",
            status="delivered",
            total_amount=129.00,
            estimated_delivery="2026-08-25",
        ),
        Order(
            id=1044,
            customer_email="michael@example.com",
            status="processing",
            total_amount=899.00,
            estimated_delivery="2026-09-02",
        ),
    ]

    db = SessionLocal()

    try:
        for order in orders:
            existing_order = db.scalar(
                select(Order).where(
                    Order.id == order.id
                )
            )

            if existing_order is None:
                db.add(order)

        db.commit()

        print("Sample orders created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_orders()