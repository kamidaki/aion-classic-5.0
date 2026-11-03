package com.aionemu.gameserver.model.templates.item;

import java.util.Collections;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlList;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;

/**
 * Um set do client_disassembly_item 5.0: sorteado sozinho com rate/1000 e, se passar, da um dos seus itens escolhido pelo peso (a
 * disassemble_set_list aponta para uma lista do client_disassembly_item_SetList, cujos rates somam 10000).
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DecomposableSet")
public class DecomposableSet {

	@XmlElement(name = "item")
	private List<DecomposableSetItem> items;
	@XmlAttribute(name = "rate")
	private int rate = 1000;
	@XmlAttribute(name = "race")
	private Race race = Race.PC_ALL;
	@XmlList
	@XmlAttribute(name = "player_classes")
	private List<PlayerClass> playerClasses;
	@XmlAttribute(name = "minlevel")
	private int minLevel;
	@XmlAttribute(name = "maxlevel")
	private int maxLevel = 99;

	public List<DecomposableSetItem> getItems() {
		return items != null ? items : Collections.emptyList();
	}

	public int getRate() {
		return rate;
	}

	public Race getRace() {
		return race;
	}

	public boolean appliesTo(Player player) {
		return (race == Race.PC_ALL || race == player.getRace())
			&& (playerClasses == null || playerClasses.contains(player.getPlayerClass()))
			&& player.getLevel() >= minLevel && player.getLevel() <= maxLevel;
	}

	public boolean roll() {
		return rate >= 1000 || Rnd.get(1, 1000) <= rate;
	}

	public DecomposableSetItem pickItem() {
		int total = 0;
		for (DecomposableSetItem item : getItems())
			total += item.getRate();
		if (total <= 0)
			return null;
		int roll = Rnd.nextInt(total);
		for (DecomposableSetItem item : getItems()) {
			roll -= item.getRate();
			if (roll < 0)
				return item;
		}
		return null;
	}
}
