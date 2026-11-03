package com.aionemu.gameserver.model.templates.siegelocation;

import javax.xml.bind.annotation.*;

import java.util.List;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "SiegeRelatedBases")
public class SiegeRelatedBases {

	@XmlList
	@XmlAttribute(name = "ids")
	private List<Integer> baseIds;

	public List<Integer> getBaseIds() {
		return baseIds;
	}
}
