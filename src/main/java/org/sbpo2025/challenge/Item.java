package org.sbpo2025.challenge;

import java.util.Objects; // Necesario para Objects.equals y Objects.hash

public class Item {
    private int itemId;

    public Item(int itemId) {
        this.itemId = itemId;
    }

    public int getItemId() {
        return itemId;
    }

    // Para que los objetos Item puedan ser usados como claves en Map o en Set
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Item item = (Item) o;
        return itemId == item.itemId;
    }

    @Override
    public int hashCode() {
        return Objects.hash(itemId);
    }

    @Override
    public String toString() {
        return "Item(id=" + itemId + ")";
    }
}
