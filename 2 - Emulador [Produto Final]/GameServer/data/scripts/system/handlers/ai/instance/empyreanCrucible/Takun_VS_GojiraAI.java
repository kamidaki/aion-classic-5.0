package ai.instance.empyreanCrucible;

import ai.AggressiveNpcAI;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.utils.PacketSendUtility;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Takun_VS_Gojira")
public class Takun_VS_GojiraAI extends AggressiveNpcAI
{
	private Npc counterpart;
	
	@Override
	public void handleSpawned() {
		super.handleSpawned();
		//The eyes of Takun the Terrible turn red.
		PacketSendUtility.npcSendPacketTime(getOwner(), S_MESSAGE_CODE.STR_MSG_IDArena_05, 2000);
		//The eyes of Gojira turn red.
		PacketSendUtility.npcSendPacketTime(getOwner(), S_MESSAGE_CODE.STR_MSG_IDArena_05, 6000);
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				counterpart = getPosition().getWorldMapInstance().getNpc(getNpcId() == 217596 ? 217597 : 217596);
				if (counterpart != null) {
					getAggroList().addHate(counterpart, 1000000);
				}
			}
		}, 500);
	}
}