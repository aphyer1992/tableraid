from items.item_base import Item
from items.sael_items import ALL_ITEMS

ITEM_REGISTRY: dict[str, Item] = {}

for _item in ALL_ITEMS:
    ITEM_REGISTRY[_item.id] = _item


def get_item(item_id: str) -> Item:
    item = ITEM_REGISTRY.get(item_id)
    if item is None:
        raise KeyError(f"Unknown item id: {item_id!r}")
    return item
