from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

basic_auth = HTTPBasic()

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

class User(BaseModel):
    username: str
    role: str

users = {
    "admin": {"username": "admin", "role": "Admin", "password": "adminpass"},
    "user": {"username": "user", "role": "User", "password": "userpass"}
}

items = []

def get_current_user(credentials: HTTPBasicCredentials = Depends(basic_auth)):
    user = users.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

def check_role(role: str):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker

@app.get("/items", response_model=List[Item])
def get_items(user: dict = Depends(get_current_user)):
    return items

@app.post("/items", response_model=Item)
def create_item(item: Item, user: dict = Depends(check_role("Admin"))):
    if any(i.id == item.id for i in items):
        raise HTTPException(status_code=400, detail="Item with this ID already exists")
    items.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int, user: dict = Depends(get_current_user)):
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.patch("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item_update: Item, user: dict = Depends(check_role("Admin"))):
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = item_update
            return item_update
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, user: dict = Depends(check_role("Admin"))):
    global items
    items = [item for item in items if item.id != item_id]
    return {"message": "Item deleted successfully"}
