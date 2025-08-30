package org.sbpo2025.challenge;

import java.util.Map;

public class Runner {
    private int index;
    private Map<Integer, Integer> stock; // itemId -> quantity

    public Runner(int index, Map<Integer, Integer> stock) {
        this.index = index;
        this.stock = stock;
    }

    public int getIndex() {
        return index;
    }

    public Map<Integer, Integer> getStock() {
        return stock;
    }

    @Override
    public String toString() {
        return "Runner(id=" + index + ", stock=" + stock + ")";
    }
}
