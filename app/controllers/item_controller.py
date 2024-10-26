from app.models.item_model import Item

# Dữ liệu mẫu (database giả lập)
items_db = []

class ItemController:
    @staticmethod
    def get_all_items():
        return items_db

    @staticmethod
    def get_item(item_id: int):
        return next((item for item in items_db if item.id == item_id), None)

    @staticmethod
    def create_item(item: Item):
        items_db.append(item)
        return item

    @staticmethod
    def delete_item(item_id: int):
        global items_db
        items_db = [item for item in items_db if item.id != item_id]
        return {"msg": f"Item with id {item_id} deleted"}