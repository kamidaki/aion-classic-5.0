package ai.instance.beshmundirTemple;

import ai.AggressiveNpcAI;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai2.AIName;
import com.aionemu.gameserver.ai2.AI2Actions;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.knownlist.Visitor;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("magicartifact")
public class Magic_ArtifactAI extends AggressiveNpcAI
{
	private boolean cooldown = false;
	
	@Override
	protected void handleAttack(Creature creature) {
		super.handleAttack(creature);
		if (!cooldown) {
			announceMagicArtifact();
			AI2Actions.useSkill(this, 18916);
			setCD();
		}
	}
	
	private void setCD() {
		cooldown = true;
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				cooldown = false;
			}
		}, 1000);
	}
	
	private void announceMagicArtifact() {
		getPosition().getWorldMapInstance().doOnAllPlayers(new Visitor<Player>() {
			@Override
			public void visit(Player player) {
				if (player.isOnline()) {
					//The Magic Artifact has been activated!
					PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_MSG_IDCatacombs_Boss_ArchPriest_Artifact_Dark);
				}
			}
		});
	}
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}