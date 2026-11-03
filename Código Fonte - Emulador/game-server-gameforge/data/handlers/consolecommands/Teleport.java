package consolecommands;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.chathandlers.ConsoleCommand;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMapInstance;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * @author Lost Academy Team & Durak
 */
public class Teleport extends ConsoleCommand {

	public Teleport() {
		super("teleport", "Moves you to any location.");

		setSyntaxInfo("[mapCName] <x> <y> <z> - Moves you to the specified coordinates on the given map (default: current map).");
	}

	@Override
	protected void execute(Player player, String... params) {
		if (params.length < 3) {
			sendInfo(player);
			return;
		}
		int i = 0;
		int worldId = params.length == 3 ? player.getWorldId() : DataManager.WORLD_MAPS_DATA.getWorldIdByCName(params[i++]);
		if (worldId != 0) {
			int x = Integer.parseInt(params[i++]);
			int y = Integer.parseInt(params[i++]);
			int inputZ = Integer.parseInt(params[i++]);
			float z = inputZ;
			WorldMapInstance instance = getOrCreateWorldMapInstance(player, worldId);
			if (inputZ == 10_000) // default value in client when selecting a point on the world map
				z = GeoService.getInstance().getZ(worldId, x, y, 4000f, 0f, instance.getInstanceId());
			TeleportService.teleportTo(player, instance, x, y, z);
		}
	}

	private WorldMapInstance getOrCreateWorldMapInstance(Player player, int worldId) {
		if (player.getWorldId() == worldId)
			return player.getPosition().getWorldMapInstance();
		else if (World.getInstance().getWorldMap(worldId).isInstanceType())
			return InstanceService.getOrRegisterInstance(worldId, player);
		else
			return World.getInstance().getWorldMap(worldId).getMainWorldMapInstance();
	}
}
