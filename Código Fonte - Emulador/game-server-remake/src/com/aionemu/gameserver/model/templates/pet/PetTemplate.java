package com.aionemu.gameserver.model.templates.pet;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

import com.aionemu.gameserver.model.templates.L10n;
import com.aionemu.gameserver.model.templates.VisibleObjectTemplate;
import com.aionemu.gameserver.model.templates.stats.PetStatsTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.NONE)
@XmlRootElement(name = "pet")
public class PetTemplate extends VisibleObjectTemplate implements L10n {

	@XmlAttribute(name = "id", required = true)
	private int id;

	@XmlAttribute(name = "name_en")
	private String nameEn;

	@XmlAttribute(name = "name_pt")
	private String namePt;

	@Deprecated
	@XmlAttribute(name = "name")
	private String name;

	@XmlAttribute(name = "nameid", required = true)
	private int nameId;

	@XmlAttribute(name = "condition_reward")
	private int conditionReward;

	@XmlElement(name = "petfunction")
	private List<PetFunction> petFunctions;

	@XmlElement(name = "petstats")
	private PetStatsTemplate petStats;

	@XmlTransient
	Boolean hasPlayerFuncs = null;

	@Override
	public int getTemplateId() {
		return id;
	}

	@Override
	public String getName() {
		if (namePt != null && !namePt.isEmpty()) {
			return namePt;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return nameEn == null ? "" : nameEn;
	}

	@Override
	public String getNameEn() {
		if (nameEn != null && !nameEn.isEmpty()) {
			return nameEn;
		}
		if (name != null && !name.isEmpty()) {
			return name;
		}
		return namePt == null ? "" : namePt;
	}

	@Override
	public int getL10nId() {
		return nameId;
	}

	public List<PetFunction> getPetFunctions() {
		if (hasPlayerFuncs == null) {
			hasPlayerFuncs = false;
			if (petFunctions == null) {
				List<PetFunction> result = new ArrayList<>();
				result.add(PetFunction.CreateEmpty());
				petFunctions = result;
			} else {
				for (PetFunction func : petFunctions) {
					if (func.getPetFunctionType().isPlayerFunction()) {
						hasPlayerFuncs = true;
						break;
					}
				}
				if (!hasPlayerFuncs)
					petFunctions.add(PetFunction.CreateEmpty());
			}
		}
		return petFunctions;
	}

	public PetFunction getWarehouseFunction() {
		if (petFunctions == null)
			return null;
		for (PetFunction pf : petFunctions) {
			if (pf.getPetFunctionType() == PetFunctionType.WAREHOUSE)
				return pf;
		}
		return null;
	}

	/**
	 * Used to write to SM_PET packet, so checks only needed ones
	 */
	public boolean containsFunction(PetFunctionType type) {
		if (type.getId() < 0)
			return false;

		for (PetFunction t : getPetFunctions()) {
			if (t.getPetFunctionType() == type)
				return true;
		}
		return false;
	}

	/**
	 * Returns function if found, otherwise null
	 */
	public PetFunction getPetFunction(PetFunctionType type) {
		for (PetFunction t : getPetFunctions()) {
			if (t.getPetFunctionType() == type)
				return t;
		}
		return null;
	}

	public PetStatsTemplate getPetStats() {
		return petStats;
	}

	public final int getConditionReward() {
		return conditionReward;
	}

}
