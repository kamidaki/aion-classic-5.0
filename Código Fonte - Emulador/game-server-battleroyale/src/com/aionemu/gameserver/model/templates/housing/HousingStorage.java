package com.aionemu.gameserver.model.templates.housing;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "HousingStorage")
public class HousingStorage extends PlaceableHouseObject {

	@XmlAttribute(name = "warehouse_id", required = true)
	protected int warehouseId;

	/**
	 * Gets the value of the warehouseId property.
	 */
	public int getWarehouseId() {
		return warehouseId;
	}

	@Override
	public byte getTypeId() {
		return 2;
	}

}
