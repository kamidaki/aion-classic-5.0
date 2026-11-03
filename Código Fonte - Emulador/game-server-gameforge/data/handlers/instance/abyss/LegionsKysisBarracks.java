package instance.abyss;

import com.aionemu.gameserver.instance.handlers.InstanceID;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * @author Lost Academy Team & Durak
 */
@InstanceID(301240000)
public class LegionsKysisBarracks extends KysisBarracks {

	public LegionsKysisBarracks(WorldMapInstance instance) {
		super(instance);
	}

	@Override
	protected int getChestId() {
		return 702294;
	}
}
