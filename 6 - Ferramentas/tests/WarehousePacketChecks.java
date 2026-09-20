import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.SM_WAREHOUSE_INFO;

/** Regression: a populated account warehouse must never exceed the client's 8192-byte frame limit. */
class WarehousePacketChecks {
    private static int checks;
    private static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static ByteBuffer payload(SM_WAREHOUSE_INFO packet) throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(65536).order(ByteOrder.LITTLE_ENDIAN);
        packet.setBuf(buffer);
        var method = SM_WAREHOUSE_INFO.class.getDeclaredMethod("writeImpl", AionConnection.class);
        method.setAccessible(true);
        method.invoke(packet, new Object[] { null });
        buffer.flip();
        return buffer;
    }
    public static void main(String[] args) throws Exception {
        var template = new ItemTemplate();
        var id = ItemTemplate.class.getDeclaredField("itemId");
        id.setAccessible(true);
        id.setInt(template, 166300000);
        List<Item> items = new ArrayList<>();
        for (int i = 0; i < 250; i++) {
            Item item = new Item(i + 1, template, 4, false, i);
            if (i % 3 == 0) item.setItemCreator("Criador".repeat(10));
            items.add(item);
        }
        var packets = SM_WAREHOUSE_INFO.split(items, 2, 3, null);
        check(packets.size() > 1, "Large warehouse is split");
        int expectedId = 1;
        for (int i = 0; i < packets.size(); i++) {
            ByteBuffer buffer = payload(packets.get(i));
            check(buffer.remaining() + 7 <= 8192, "Frame respects client limit");
            check(buffer.get() == 2, "Storage type preserved");
            check(buffer.get() == (i == 0 ? 1 : 0), "Only first packet resets storage");
            check(buffer.get() == 3, "Expansion preserved");
            buffer.getShort();
            int count = Short.toUnsignedInt(buffer.getShort());
            for (int j = 0; j < count; j++) {
                check(buffer.getInt() == expectedId++, "No duplicated, missing or reordered items");
                check(buffer.getInt() == 166300000, "Template preserved");
                buffer.get();
                int blobSize = Short.toUnsignedInt(buffer.getShort());
                buffer.position(buffer.position() + blobSize);
                check(Short.toUnsignedInt(buffer.getShort()) == expectedId - 2, "Slot preserved");
            }
            check(!buffer.hasRemaining(), "Declared count matches complete serialized entries");
        }
        check(expectedId == 251, "Every item delivered exactly once");
        var empty = SM_WAREHOUSE_INFO.split(List.of(), 2, 0, null);
        check(empty.size() == 1 && payload(empty.getFirst()).remaining() == 7, "Empty storage initializes once");
        var snapshot = SM_WAREHOUSE_INFO.split(items.subList(0, 1), 2, 0, null).getFirst();
        byte[] before = payload(snapshot).array().clone();
        items.getFirst().setItemCreator("Alterado depois do envio");
        check(java.util.Arrays.equals(before, payload(snapshot).array()), "Queued payload does not change after partitioning");
        try {
            new SM_WAREHOUSE_INFO(items, 2, 0, true, null);
            throw new AssertionError("Oversized unsplit packet accepted");
        } catch (IllegalArgumentException expected) {
            check(true, "Unsplit oversize cannot reach client");
        }
        System.out.println("PASS: " + checks + " warehouse packet checks");
    }
}
