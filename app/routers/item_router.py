from fastapi import APIRouter, HTTPException
from app.controllers.item_controller import ItemController
from app.models.item_model import Item

router = APIRouter()

@router.get("/items")
def get_items():
    return ItemController.get_all_items()

@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = ItemController.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/items")
def create_item(item: Item):
    return ItemController.create_item(item)

@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    return ItemController.delete_item(item_id)