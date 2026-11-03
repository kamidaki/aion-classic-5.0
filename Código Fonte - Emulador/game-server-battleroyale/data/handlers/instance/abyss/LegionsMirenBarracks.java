package instance.abyss;

import com.aionemu.gameserver.instance.handlers.InstanceID;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * @author Lost Academy Team & Durak
 */
@InstanceID(301250000)
public class LegionsMirenBarracks extends MirenBarracks {

	public LegionsMirenBarracks(WorldMapInstance instance) {
		super(instance);
	}

	@Override
	protected int getChestId() {
		return 702298;
	}
}
