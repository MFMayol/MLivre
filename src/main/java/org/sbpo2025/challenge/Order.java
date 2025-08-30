package org.sbpo2025.challenge;

import java.util.Map;
import java.util.stream.Collectors; // Necesario para Collectors.summingInt

public class Order {
    private int index;
    private Map<Integer, Integer> items; // itemId -> quantity

    public Order(int index, Map<Integer, Integer> items) {
        this.index = index;
        this.items = items;
    }

    public int getIndex() {
        return index;
    }

    public Map<Integer, Integer> getItems() {
        return items;
    }

    // Equivalente a get_total_items en Python
    public int getTotalItems() {
        return items.values().stream().mapToInt(Integer::intValue).sum();
    }

    @Override
    public String toString() {
        return "Order(id=" + index + ", items=" + items + ")";
    }
}
