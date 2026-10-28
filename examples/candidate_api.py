from fastapi import FastAPI

app = FastAPI(title="ChangeShield Replay Candidate")


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    return {"id": order_id, "quantity": 2}


@app.post("/orders", status_code=201)
def create_order(payload: dict):
    return {"id": "new-order", "product_id": payload.get("product_id"), "quantity": payload.get("quantity")}
