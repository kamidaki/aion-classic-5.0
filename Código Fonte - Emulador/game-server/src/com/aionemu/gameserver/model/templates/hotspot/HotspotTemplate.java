package com.aionemu.gameserver.model.templates.hotspot;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Race;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Hotspot")
public class HotspotTemplate {

	@XmlAttribute(name = "id")
	protected int id;

	@XmlAttribute(name = "worldId")
	protected int worldId;

	@XmlAttribute(name = "x")
	protected float x;

	@XmlAttribute(name = "y")
	protected float y;

	@XmlAttribute(name = "z")
	protected float z;

	@XmlAttribute(name = "race")
	protected Race race;

	@XmlAttribute(name = "price")
	protected long price;

	/** custo extra por metro até o destino (required_distance_gold do client_zonemap_hotspot) */
	@XmlAttribute(name = "distance_price")
	protected float distancePrice;

	@XmlAttribute(name = "min_level")
	protected int minLevel;

	@XmlAttribute(name = "h")
	protected byte heading;

	public int getId() {
		return id;
	}

	public int getWorldId() {
		return worldId;
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

	public Race getRace() {
		return race;
	}

	public long getPrice() {
		return price;
	}

	public float getDistancePrice() {
		return distancePrice;
	}

	public int getMinLevel() {
		return minLevel;
	}

	public byte getHeading() {
		return heading;
	}
}
