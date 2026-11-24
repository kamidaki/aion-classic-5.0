package com.aionemu.gameserver.model.gameobjects.player;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;

/**
 * Um visual guardado no Wardrobe: o template do item registrado, a tinta e a marca de favorito. A cor segue o formato do {@link
 * com.aionemu.gameserver.model.gameobjects.Item}: RGB sem alfa, ou null sem tinta (há tinta preta, 000000, então 0 não serve de "sem cor").
 */
public class WardrobeEntry {

	private final int objectId;
	private final int itemId;
	private Integer color;
	private boolean liked;

	public WardrobeEntry(int objectId, int itemId, Integer color, boolean liked) {
		this.objectId = objectId;
		this.itemId = itemId;
		this.color = color == null ? null : color & 0xFFFFFF;
		this.liked = liked;
	}

	public int getItemId() {
		return itemId;
	}

	public int getObjectId() {
		return objectId;
	}

	public boolean isLiked() {
		return liked;
	}

	public void setLiked(boolean liked) {
		this.liked = liked;
	}

	/**
	 * @return RGB ou null sem tinta
	 */
	public Integer getColor() {
		return color;
	}

	public void setColor(Integer color) {
		this.color = color == null ? null : color & 0xFFFFFF;
	}

	/**
	 * Cor como fica na coluna player_wardrobe.color (NOT NULL): 0x01RRGGBB, ou 0 sem tinta.
	 */
	public int getStoredColor() {
		return color == null ? 0 : 0x1000000 | color;
	}

	public static Integer fromStoredColor(int stored) {
		return (stored & 0x1000000) == 0 ? null : stored & 0xFFFFFF;
	}

	public ItemTemplate getItemSkinTemplate() {
		return DataManager.ITEM_DATA.getItemTemplate(this.itemId);
	}
}
