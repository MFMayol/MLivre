package org.sbpo2025.challenge;

public class Picking {
    private int orderIndex;
    private int itemId;
    private int quantity;
    private int runnerIndex;

    public Picking(int orderIndex, int itemId, int quantity, int runnerIndex) {
        this.orderIndex = orderIndex;
        this.itemId = itemId;
        this.quantity = quantity;
        this.runnerIndex = runnerIndex;
    }

    public int getOrderIndex() {
        return orderIndex;
    }

    public int getItemId() {
        return itemId;
    }

    public int getQuantity() {
        return quantity;
    }

    public int getRunnerIndex() {
        return runnerIndex;
    }

    @Override
    public String toString() {
        return "Picking(order=" + orderIndex + ", item=" + itemId + ", qty=" + quantity + ", runner=" + runnerIndex + ")";
    }
}
