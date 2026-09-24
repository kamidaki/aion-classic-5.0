package com.aionemu.gameserver.model;

import javax.xml.bind.annotation.XmlEnum;

/**
 * @author Lost Academy Team & Durak
 */
@XmlEnum
public enum Gender {
	/**
	 * Males
	 */
	MALE(0),

	/**
	 * Females
	 */
	FEMALE(1);

	/**
	 * id of gender
	 */
	private int genderId;

	/**
	 * Constructor.
	 * 
	 * @param genderId
	 *          id of the gender
	 */
	private Gender(int genderId) {
		this.genderId = genderId;
	}

	/**
	 * Get id of this gender.
	 * 
	 * @return gender id
	 */
	public int getGenderId() {
		return genderId;
	}
}
