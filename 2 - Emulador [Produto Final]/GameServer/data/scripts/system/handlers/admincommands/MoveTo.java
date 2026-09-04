package admincommands;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.teleport.TeleportService2;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * Admin moveto command
 * 
 * @author KID
 */
public class MoveTo extends AdminCommand {

	public MoveTo() {
		super("moveto");
	}

	@Override
	public void execute(Player admin, String... params) {
		if (params == null || params.length < 4) {
			PacketSendUtility.sendMessage(admin, "syntax //moveto worldId X Y Z");
			return;
		}

		int worldId;
		float x, y, z;

		try {
			worldId = Integer.parseInt(params[0]);
			x = Float.parseFloat(params[1]);
			y = Float.parseFloat(params[2]);
			z = Float.parseFloat(params[3]);
		}
		catch (NumberFormatException e) {
			PacketSendUtility.sendMessage(admin, "All the parameters should be numbers");
			return;
		}

		// Validar contra o world_maps.xml, nao contra o enum WorldMapType: o enum e uma lista
		// cravada a mao com 95 mapas, herdada do 4.8, enquanto o XML carrega 145 -- entre os que
		// faltam no enum esta o 390000000, o mapa do tutorial do Classic 5.0. Quem decide se um
		// mapa existe e o dado, nao a lista.
		if (DataManager.WORLD_MAPS_DATA.getTemplate(worldId) == null) {
			PacketSendUtility.sendMessage(admin, "O mapa " + worldId + " nao existe no world_maps.xml.");
		}
		else {
			TeleportService2.teleportTo(admin, worldId, x, y, z);
			PacketSendUtility.sendMessage(admin, "Teleported to " + x + " " + y + " " + z + " [" + worldId + "]");
		}
	}

	@Override
	public void onFail(Player player, String message) {
		PacketSendUtility.sendMessage(player, "syntax //moveto worldId X Y Z");
	}
}
