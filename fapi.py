from fastapi import FastAPI, HTTPException, Depends
from typing import Dict
import asyncio

app = FastAPI()

# Mock databases
products = {
    "1": {"name": "Laptop", "price": 1000},
    "2": {"name": "Phone", "price": 500},
}

user_profiles = {
    "1": {"user_id": "1", "name": "Alice", "email": "alice@example.com", "balance": 1000.0},
    "2": {"user_id": "2", "name": "Bob", "email": "bob@example.com", "balance": 500.0},
}

# Mock authentication (insecure for demonstration)
def get_current_user(user_id: str = None) -> dict:
    # In a real app, this would come from an authentication token
    if user_id not in user_profiles:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_profiles[user_id]

# IDOR Vulnerability
@app.get("/profile/{profile_id}")
async def get_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    # IDOR vulnerability: Any user can access any profile by modifying the profile_id
    if profile_id not in user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user_profiles[profile_id]

# Business Logic Vulnerability
@app.post("/apply_discount/")
async def apply_discount(product_id: str, discount: float, current_user: dict = Depends(get_current_user)):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    # Business logic vulnerability: No proper validation for discount
    product = products[product_id]
    new_price = product["price"] - product["price"] * discount

    # This allows excessive discounts like 100% off or even negative prices
    if new_price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    return {"user": current_user["name"], "product": product["name"], "original_price": product["price"], "new_price": new_price}

# Race Condition Vulnerability
@app.post("/transfer/")
async def transfer_funds(from_user: str, to_user: str, amount: float):
    if from_user not in user_profiles or to_user not in user_profiles:
        raise HTTPException(status_code=404, detail="User not found")

    if user_profiles[from_user]["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Simulate delay (e.g., database write operation)
    await asyncio.sleep(1)

    # Deduct amount from sender
    user_profiles[from_user]["balance"] -= amount

    # Add amount to receiver
    user_profiles[to_user]["balance"] += amount

    return {
        "from_user": from_user,
        "to_user": to_user,
        "transferred_amount": amount,
        "sender_balance": user_profiles[from_user]["balance"],
        "receiver_balance": user_profiles[to_user]["balance"],
    }
