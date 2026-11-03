package instance.abyss;

import com.aionemu.gameserver.instance.handlers.InstanceID;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * @author Lost Academy Team & Durak
 */
@InstanceID(301260000)
public class LegionsKrotanBarracks extends KrotanBarracks {

	public LegionsKrotanBarracks(WorldMapInstance instance) {
		super(instance);
	}

	@Override
	protected int getChestId() {
		return 702290;
	}
}
