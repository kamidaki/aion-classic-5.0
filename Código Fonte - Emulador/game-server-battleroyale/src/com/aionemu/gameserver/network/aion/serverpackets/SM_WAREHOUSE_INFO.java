package com.aionemu.gameserver.network.aion.serverpackets;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.services.StigmaService;

public class SM_WAREHOUSE_INFO extends AionServerPacket {

    private static final int HEADER_SIZE = 7;
    private static final int MAX_ITEMS_SIZE = MAX_USABLE_PACKET_BODY_SIZE - HEADER_SIZE;
    private final int warehouseType;
    private final List<byte[]> entries;
    private final boolean firstPacket;
    private final int expandLvl;

    public SM_WAREHOUSE_INFO(Collection<Item> items, int warehouseType, int expandLvl, boolean firstPacket, Player player) {
        this(warehouseType, expandLvl, firstPacket, encode(items, warehouseType, player));
    }

    private SM_WAREHOUSE_INFO(int warehouseType, int expandLvl, boolean firstPacket, List<byte[]> entries) {
        this.warehouseType = warehouseType;
        this.expandLvl = expandLvl;
        this.firstPacket = firstPacket;
        this.entries = List.copyOf(entries);
        if (entries.stream().mapToInt(e -> e.length).sum() > MAX_ITEMS_SIZE)
            throw new IllegalArgumentException("Warehouse contents require split packets");
    }

    /** Split by actual serialized bytes; variable item blobs make fixed item counts unsafe. */
    public static List<SM_WAREHOUSE_INFO> split(Collection<Item> items, int warehouseType, int expandLvl, Player player) {
        List<SM_WAREHOUSE_INFO> packets = new ArrayList<>();
        List<byte[]> part = new ArrayList<>();
        int bytes = 0;
        for (byte[] entry : encode(items, warehouseType, player)) {
            if (bytes + entry.length > MAX_ITEMS_SIZE) {
                packets.add(new SM_WAREHOUSE_INFO(warehouseType, expandLvl, packets.isEmpty(), part));
                part = new ArrayList<>();
                bytes = 0;
            }
            part.add(entry);
            bytes += entry.length;
        }
        // Empty storage still needs its initialization packet. Callers retain their existing terminators.
        packets.add(new SM_WAREHOUSE_INFO(warehouseType, expandLvl, packets.isEmpty(), part));
        return packets;
    }

    private static List<byte[]> encode(Collection<Item> items, int warehouseType, Player player) {
        List<byte[]> entries = new ArrayList<>();
        if (items == null)
            return entries;
        for (Item item : items) {
            ByteBuffer buffer = ByteBuffer.allocate(MAX_CLIENT_SUPPORTED_PACKET_SIZE).order(ByteOrder.LITTLE_ENDIAN);
            buffer.putInt(item.getObjectId());
            buffer.putInt(item.getItemTemplate().getTemplateId());
            buffer.put((byte) 0); // Classic 5.0 warehouse category byte
            ItemInfoBlob.getFullBlob(player, item).writeMe(buffer);
            int slot = warehouseType == StorageType.STIGMA.getId()
                ? StigmaService.getStigmaSlotIndex(item.getEquipmentSlot()) : (int) (item.getEquipmentSlot() & 0xFFFF);
            buffer.putShort((short) slot);
            if (buffer.position() > MAX_ITEMS_SIZE)
                throw new IllegalArgumentException("Warehouse item exceeds packet limit: " + item.getItemId());
            entries.add(Arrays.copyOf(buffer.array(), buffer.position()));
        }
        return entries;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeC(warehouseType);
        writeC(firstPacket ? 1 : 0);
        writeC(expandLvl);
        writeH(0);
        writeH(entries.size());
        for (byte[] entry : entries)
            getBuf().put(entry);
    }
}
