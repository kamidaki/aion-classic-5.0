package com.aionemu.gameserver.model.templates.gather;

import java.util.ArrayList;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;
import java.util.List;


@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Exmaterials", propOrder = { "material" })
public class ExMaterials {

	protected List<Material> material;

	public List<Material> getMaterial() {
		if (material == null) {
			material = new ArrayList<Material>();
		}
		return this.material;
	}
}
