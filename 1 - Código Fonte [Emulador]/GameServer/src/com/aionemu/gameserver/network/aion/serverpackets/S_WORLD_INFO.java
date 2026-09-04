package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.controllers.RVController;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.Map;

public class S_WORLD_INFO extends AionServerPacket
{
	private int actionId;
	private RVController rift;
	private Map<Integer, Integer> rifts;
	private int gelkmaros, inggison;
	private int objectId;
	
	public S_WORLD_INFO(Map<Integer, Integer> rifts) {
		this.actionId = 0;
		this.rifts = rifts;
	}
	
	public S_WORLD_INFO(boolean gelkmaros, boolean inggison) {
        this.gelkmaros = gelkmaros ? 1 : 0;
        this.inggison = inggison ? 1 : 0;
        this.actionId = 1;
    }
	
	public S_WORLD_INFO(RVController rift, boolean isMaster) {
		this.rift = rift;
		this.actionId = isMaster ? 2 : 3;
	}
	
	public S_WORLD_INFO(int objectId) {
        this.objectId = objectId;
        this.actionId = 4;
    }
	
	@Override
	protected void writeImpl(AionConnection con) {
		switch (actionId) {
			case 0:
				writeH(0x09);
				writeC(actionId);
				for (int value : rifts.values()) {
					writeD(value);
					writeD(0);
				}
			break;
			case 1:
                writeH(0x09);
                writeC(actionId);
                writeD(gelkmaros);
                writeD(inggison);
            break;
			case 2:
				writeH(0x21);
				writeC(actionId);
				writeD(rift.getOwner().getObjectId());
				writeD(rift.getMaxEntries()-rift.getUsedEntries());
				writeD(rift.getRemainTime());
				writeD(rift.getMinLevel());
				writeD(rift.getMaxLevel());
				writeF(rift.getOwner().getX());
				writeF(rift.getOwner().getY());
				writeF(rift.getOwner().getZ());
			break;
			case 3:
				writeH(0x0D);
                writeC(actionId);
                writeD(rift.getOwner().getObjectId());
                writeD(rift.getUsedEntries());
                writeD(rift.getRemainTime());
			break;
			case 4:
				writeH(0x05);
				writeC(actionId);
				writeD(objectId);
			break;
		}
	}
}