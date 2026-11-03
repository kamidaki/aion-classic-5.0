package com.aionemu.gameserver.model.templates;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.stats.calc.StatOwner;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.stats.ModifiersTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.NONE)
public class TitleTemplate implements StatOwner, L10n {

	@XmlAttribute(name = "id", required = true)
	private int titleId;
	@XmlElement(name = "modifiers")
	protected ModifiersTemplate modifiers;
	@XmlAttribute(name = "race", required = true)
	private Race race;
	@XmlAttribute(name = "nameId")
	private int nameId;
	@XmlAttribute(name = "desc_en")
	private String descEn;
	@XmlAttribute(name = "desc_pt")
	private String descPt;
	@XmlAttribute(name = "name_en")
	private String nameEn;
	@XmlAttribute(name = "name_pt")
	private String namePt;
	@XmlAttribute(name = "desc")
	private String description;
	@XmlAttribute(name = "available")
	private Boolean available;

	public int getTitleId() {
		return titleId;
	}

	public Race getRace() {
		return race;
	}

	@Override
	public int getL10nId() {
		return nameId;
	}

	public String getDesc() {
		if (descPt != null && !descPt.isEmpty()) {
			return descPt;
		}
		if (namePt != null && !namePt.isEmpty()) {
			return namePt;
		}
		if (description != null && !description.isEmpty()) {
			return description;
		}
		return descEn != null ? descEn : (nameEn != null ? nameEn : "");
	}

	public String getDescEn() {
		if (descEn != null && !descEn.isEmpty()) {
			return descEn;
		}
		if (nameEn != null && !nameEn.isEmpty()) {
			return nameEn;
		}
		if (description != null && !description.isEmpty()) {
			return description;
		}
		return descPt != null ? descPt : (namePt != null ? namePt : "");
	}

	public String getName() {
		return getDesc();
	}

	public String getNameEn() {
		return getDescEn();
	}

	/** Whether this title exists in the current client catalog. */
	public boolean isAvailable() {
		return available == null || available;
	}

	public List<StatFunction> getModifiers() {
		return modifiers == null ? null : modifiers.getModifiers();
	}
}
