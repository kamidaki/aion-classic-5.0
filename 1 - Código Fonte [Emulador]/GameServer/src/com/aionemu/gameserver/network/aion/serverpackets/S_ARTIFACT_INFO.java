package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.siege.ArtifactLocation;
import com.aionemu.gameserver.model.siege.SiegeLocation;
import com.aionemu.gameserver.model.siege.SiegeType;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.SiegeService;
import javolution.util.FastList;

import java.util.ArrayList;
import java.util.Collection;

public class S_ARTIFACT_INFO extends AionServerPacket
{
	private boolean teleportStatus;
	private Collection<ArtifactLocation> locations;

	public S_ARTIFACT_INFO(Collection<ArtifactLocation> collection) {
		this.locations = collection;
	}

	public S_ARTIFACT_INFO(int loc) {
		locations = new ArrayList<ArtifactLocation>();
		locations.add(SiegeService.getInstance().getArtifact(loc));
	}

	public S_ARTIFACT_INFO(int locationId, boolean teleportStatus) {
		locations = new ArrayList<ArtifactLocation>();
		locations.add(SiegeService.getInstance().getArtifact(locationId));
		this.teleportStatus = teleportStatus;
	}


	@Override
	protected void writeImpl(AionConnection con) {
		writeH(locations.size());
		for (ArtifactLocation artifact : locations) {
			writeD(artifact.getLocationId() * 10 + 1);
			writeC(artifact.getStatus().getValue());
			writeD(0);
			//writeC(teleportStatus ? 1 : 0);
		}
	}
}