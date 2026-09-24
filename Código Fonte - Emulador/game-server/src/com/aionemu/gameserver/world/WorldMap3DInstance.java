package com.aionemu.gameserver.world;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import com.aionemu.gameserver.instance.handlers.InstanceHandler;
import com.aionemu.gameserver.world.zone.ZoneInstance;

/**
 * @author Lost Academy Team & Durak
 */
public class WorldMap3DInstance extends WorldMapInstance {

	public WorldMap3DInstance(WorldMap parent, int instanceId, int maxPlayers, Function<WorldMapInstance, InstanceHandler> instanceHandlerSupplier) {
		super(parent, instanceId, maxPlayers, instanceHandlerSupplier);
	}

	@Override
	public MapRegion getRegion(float x, float y, float z) {
		int size = getParent().getWorldSize();
		float maxZ = Math.round((float) size / regionSize) * regionSize;
		float clampedX = Math.max(0, Math.min(size - 1, x));
		float clampedY = Math.max(0, Math.min(size - 1, y));
		float clampedZ = Math.max(0, Math.min(maxZ - 1, z));
		int regionId = RegionUtil.get3dRegionId(clampedX, clampedY, clampedZ);
		MapRegion region = regions.get(regionId);
		if (region == null) {
			regionId = RegionUtil.get3dRegionId(x, y, z);
			region = regions.get(regionId);
		}
		return region;
	}

	@Override
	protected void initMapRegions() {
		int size = getParent().getWorldSize();
		float maxZ = Math.round((float) size / regionSize) * regionSize;

		List<Integer> regionIds = new ArrayList<>();
		for (int x = 0; x <= size; x = x + regionSize) {
			for (int y = 0; y <= size; y = y + regionSize) {
				for (int z = 0; z < maxZ; z = z + regionSize) {
					regionIds.add(RegionUtil.get3dRegionId(x, y, z));
				}
			}
		}
		regionIds.parallelStream().forEach(regionId -> {
			MapRegion mapRegion = createMapRegion(regionId);
			synchronized (regions) {
					regions.put(regionId, mapRegion);
			}
		});

		// Add Neighbour
		for (int x = 0; x <= size; x = x + regionSize) {
			for (int y = 0; y <= size; y = y + regionSize) {
				for (int z = 0; z < maxZ; z = z + regionSize) {
					int regionId = RegionUtil.get3dRegionId(x, y, z);
					MapRegion mapRegion = regions.get(regionId);
					for (int x2 = x - regionSize; x2 <= x + regionSize; x2 += regionSize) {
						for (int y2 = y - regionSize; y2 <= y + regionSize; y2 += regionSize) {
							for (int z2 = z - regionSize; z2 < z + regionSize; z2 += regionSize) {
								if (x2 == x && y2 == y && z2 == z)
									continue;
								int neighbourId = RegionUtil.get3dRegionId(x2, y2, z2);
								MapRegion neighbour = regions.get(neighbourId);
								if (neighbour != null)
									mapRegion.addNeighbourRegion(neighbour);
							}
						}
					}
				}
			}
		}
	}

	@Override
	protected MapRegion createMapRegion(int regionId) {
		float startX = RegionUtil.getXFrom3dRegionId(regionId);
		float startY = RegionUtil.getYFrom3dRegionId(regionId);
		float startZ = RegionUtil.getZFrom3dRegionId(regionId);
		ZoneInstance[] zones = filterZones(this.getMapId(), regionId, startX, startY, startZ, startZ + regionSize);
		return new MapRegion(regionId, this, zones);
	}

	@Override
	public boolean isPersonal() {
		return false;
	}

	@Override
	public int getOwnerId() {
		return 0;
	}
}
