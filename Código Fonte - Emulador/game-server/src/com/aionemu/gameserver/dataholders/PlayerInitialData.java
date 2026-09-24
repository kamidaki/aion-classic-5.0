package com.aionemu.gameserver.dataholders;

import java.util.*;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;

import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "player_initial_data")
@XmlAccessorType(XmlAccessType.FIELD)
public class PlayerInitialData {

	@XmlElement(name = "player_data")
	private List<PlayerCreationData> dataList;

	@XmlElement(name = "elyos_spawn_location", required = true)
	private LocationData elyosSpawnLocation;
	@XmlElement(name = "asmodian_spawn_location", required = true)
	private LocationData asmodianSpawnLocation;
	@XmlElement(name = "elyos_telos_location", required = false)
	private LocationData elyosTelosSpawnLocation;
	@XmlElement(name = "asmodian_telos_location", required = false)
	private LocationData asmodianTelosSpawnLocation;

	@XmlTransient
	private final Map<PlayerClass, PlayerCreationData> data = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (PlayerCreationData pt : dataList) {
			data.put(pt.getRequiredPlayerClass(), pt);
		}
		dataList = null;
	}

	public PlayerCreationData getPlayerCreationData(PlayerClass cls) {
		PlayerCreationData res = data.get(cls);
		if (res == null && cls != null && cls.getStartingClass() != cls) {
			res = data.get(cls.getStartingClass());
		}
		return res;
	}

	public int size() {
		return data.size();
	}

	public LocationData getSpawnLocation(Race race) {
		switch (race) {
			case ASMODIANS:
				return asmodianSpawnLocation;
			case ELYOS:
				return elyosSpawnLocation;
			default:
				throw new IllegalArgumentException();
		}
	}

	public LocationData getTelosSpawnLocation(Race race) {
		switch (race) {
			case ASMODIANS:
				return asmodianTelosSpawnLocation != null ? asmodianTelosSpawnLocation : asmodianSpawnLocation;
			case ELYOS:
				return elyosTelosSpawnLocation != null ? elyosTelosSpawnLocation : elyosSpawnLocation;
			default:
				throw new IllegalArgumentException();
		}
	}

	/**
	 * Player creation data holder.
	 */
	public static class PlayerCreationData {

		@XmlAttribute(name = "class")
		private PlayerClass requiredPlayerClass;

		@XmlElement(name = "items")
		private ItemsType itemsType;

		// @XmlElement(name="shortcuts")
		// private ShortcutType shortcutData;

		PlayerClass getRequiredPlayerClass() {
			return requiredPlayerClass;
		}

		public List<ItemType> getItems() {
			return Collections.unmodifiableList(itemsType.items);
		}

		static class ItemsType {

			@XmlElement(name = "item")
			public List<ItemType> items = new ArrayList<>();
		}

		public static class ItemType {

			@XmlAttribute(name = "id")
			@XmlIDREF
			public ItemTemplate template;

			@XmlAttribute(name = "count")
			public int count;

			public ItemTemplate getTemplate() {
				return template;
			}

			public int getCount() {
				return count;
			}

			@Override
			public String toString() {
				final StringBuilder sb = new StringBuilder();
				sb.append("ItemType");
				sb.append("{template=").append(template);
				sb.append(", count=").append(count);
				sb.append('}');
				return sb.toString();
			}
		}

		// public static class ShortcutType
		// {
		// public List<Shortcut> shortcuts;
		// }
	}

	/**
	 * Location data holder.
	 */
	public static class LocationData {

		@XmlAttribute(name = "map_id")
		private int mapId;
		@XmlAttribute(name = "x")
		private float x;
		@XmlAttribute(name = "y")
		private float y;
		@XmlAttribute(name = "z")
		private float z;
		@XmlAttribute(name = "heading")
		private byte heading;

		LocationData() {
			//
		}

		public int getMapId() {
			return mapId;
		}

		public float getX() {
			return x;
		}

		public float getY() {
			return y;
		}

		public float getZ() {
			return z;
		}

		public byte getHeading() {
			return heading;
		}
	}

}
