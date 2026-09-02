/*
 * This file is part of Encom. **ENCOM FUCK OTHER SVN**
 *
 *  Encom is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Lesser Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Encom is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Lesser Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser Public License
 *  along with Encom.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlEnumValue;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Rinzler (Encom)
 */
@XmlType(name = "weapon_type")
@XmlEnum
public enum WeaponType
{
	SWORD_1H(new int[] {1, 8, 336, 342, 368}, 1),
	DAGGER_1H(new int[] {2, 9, 30, 337, 343, 369}, 1),
	MACE_1H(new int[] {3, 10, 338, 344, 370}, 1),
	BOOK_2H(new int[] {64, 1551, 1552, 1580}, 2),
	ORB_2H(new int[] {64, 1743, 1745, 1777}, 2),
	SWORD_2H(new int[] {15, 339, 345, 371}, 2),
	POLEARM_2H(new int[] {16, 340, 346, 372}, 2),
	STAFF_2H(new int[] {53, 1157, 1159, 1175}, 2),
	BOW(new int[] {17, 341, 347, 373}, 2),
	BLADE_2H(new int[] {2520}, 2),
	TOOLHOE_1H(new int[] {}, 1),
	TOOLPICK_2H(new int[] {}, 2),
	TOOLROD_2H(new int[] {}, 2),
	GUN_1H(new int[] {83, 76}, 1),
	CANNON_2H(new int[] {77}, 2),
	HARP_2H(new int[] {92, 78}, 2),
	GUN_2H(new int[] {}, 2),
	KEYBLADE_2H(new int[] {76, 79}, 2),
	KEYHAMMER_2H(new int[] {}, 2),

	// 5.0 prefix aliases
	@XmlEnumValue("1H_SWORD")
	_1H_SWORD(new int[] {1, 8, 336, 342, 368}, 1),
	@XmlEnumValue("1H_DAGGER")
	_1H_DAGGER(new int[] {2, 9, 30, 337, 343, 369}, 1),
	@XmlEnumValue("1H_MACE")
	_1H_MACE(new int[] {3, 10, 338, 344, 370}, 1),
	@XmlEnumValue("1H_TOOLHOE")
	_1H_TOOLHOE(new int[] {}, 1),
	@XmlEnumValue("1H_GUN")
	_1H_GUN(new int[] {83, 76}, 1),
	@XmlEnumValue("1H_GAUNTLET")
	_1H_GAUNTLET(new int[] {}, 1),
	@XmlEnumValue("2H_BOOK")
	_2H_BOOK(new int[] {64, 1551, 1552, 1580}, 2),
	@XmlEnumValue("2H_ORB")
	_2H_ORB(new int[] {64, 1743, 1745, 1777}, 2),
	@XmlEnumValue("2H_SWORD")
	_2H_SWORD(new int[] {15, 339, 345, 371}, 2),
	@XmlEnumValue("2H_POLEARM")
	_2H_POLEARM(new int[] {16, 340, 346, 372}, 2),
	@XmlEnumValue("2H_STAFF")
	_2H_STAFF(new int[] {53, 1157, 1159, 1175}, 2),
	@XmlEnumValue("2H_BLADE")
	_2H_BLADE(new int[] {2520}, 2),
	@XmlEnumValue("2H_CANNON")
	_2H_CANNON(new int[] {77}, 2),
	@XmlEnumValue("2H_HARP")
	_2H_HARP(new int[] {92, 78}, 2),
	@XmlEnumValue("2H_GUN")
	_2H_GUN(new int[] {}, 2),
	@XmlEnumValue("2H_KEYBLADE")
	_2H_KEYBLADE(new int[] {76, 79}, 2),
	@XmlEnumValue("2H_KEYHAMMER")
	_2H_KEYHAMMER(new int[] {}, 2),
	@XmlEnumValue("2H_TOOLPICK")
	_2H_TOOLPICK(new int[] {}, 2),
	@XmlEnumValue("2H_TOOLROD")
	_2H_TOOLROD(new int[] {}, 2),
	@XmlEnumValue("2H_DIMENSIONSWORD")
	_2H_DIMENSIONSWORD(new int[] {}, 2),
	@XmlEnumValue("2H_RUNESWORD")
	_2H_RUNESWORD(new int[] {}, 2),
	@XmlEnumValue("NOWEAPON")
	NOWEAPON(new int[] {}, 0);
	
	private int slots;
	private int[] requiredSkill;
	
	private WeaponType(int[] requiredSkills, int slots) {
		this.requiredSkill = requiredSkills;
		this.slots = slots;
	}
	
	public int[] getRequiredSkills() {
		return requiredSkill;
	}
	
	public int getRequiredSlots() {
		return slots;
	}
	
	public int getMask() {
		return 1 << this.ordinal();
	}
}