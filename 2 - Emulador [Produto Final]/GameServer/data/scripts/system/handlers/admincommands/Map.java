package admincommands;

import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.taskmanager.tasks.MovementNotifyTask;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;
import com.aionemu.gameserver.world.WorldMapInstance;



public class Map extends AdminCommand {

	public Map() {
		super("map");
	}

	@Override
	public void execute(Player admin, String... params) {
		WorldMapInstance instance = admin.getPosition().getWorldMapInstance();
		if ("freeze".equalsIgnoreCase(params[0])) {
			for (Npc npc : instance.getNpcs())
				npc.getAi().onGeneralEvent(AIEventType.FREEZE);
			PacketSendUtility.sendMessage(admin, "World map is frozen!");
		}
		else if ("unfreeze".equalsIgnoreCase(params[0])) {
			for (Npc npc : instance.getNpcs())
				npc.getAi().onGeneralEvent(AIEventType.UNFREEZE);
			PacketSendUtility.sendMessage(admin, "World map is unfrozen!");
		}
		else if ("stats".equalsIgnoreCase(params[0])) {
			for (String line : MovementNotifyTask.getInstance().dumpBroadcastStats()) 
				PacketSendUtility.sendMessage(admin, line);
		}
	}
	
	@Override
	public void onFail(Player player, String message) {
		PacketSendUtility.sendMessage(player, "usage: //map freeze | unfreeze | stats");
	}
}
