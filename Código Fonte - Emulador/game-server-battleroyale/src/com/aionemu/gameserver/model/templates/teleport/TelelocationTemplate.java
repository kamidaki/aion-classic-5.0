package com.aionemu.gameserver.model.templates.teleport;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;

import com.aionemu.gameserver.model.templates.L10n;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "teleloc_template")
@XmlAccessorType(XmlAccessType.NONE)
public class TelelocationTemplate implements L10n {

	/**
	 * Location Id.
	 */
	@XmlAttribute(name = "loc_id", required = true)
	private int locId;

	@XmlAttribute(name = "mapid", required = true)
	private int mapid = 0;

	@XmlAttribute(name = "name_id", required = true)
	private int nameId;

	@XmlAttribute(name = "name_en")
	private String nameEn;

	@XmlAttribute(name = "name_pt")
	private String namePt;

	@Deprecated
	@XmlAttribute(name = "name")
	private String name;

	@XmlAttribute(name = "posX")
	private float x = 0;

	@XmlAttribute(name = "posY")
	private float y = 0;

	@XmlAttribute(name = "posZ")
	private float z = 0;

	@XmlAttribute(name = "heading")
	private int heading = 0;

	public int getLocId() {
		return locId;
	}

	public int getMapId() {
		return mapid;
	}

	@Override
	public int getL10nId() {
		return nameId;
	}

	public String getName() {
		if (namePt != null && !namePt.isEmpty()) {
			return namePt;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return nameEn != null ? nameEn : "";
	}

	public String getNameEn() {
		if (nameEn != null && !nameEn.isEmpty()) {
			return nameEn;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return namePt != null ? namePt : "";
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

	public int getHeading() {
		return heading;
	}
}
