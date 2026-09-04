package com.aionemu.gameserver.model.templates.quest;

/****/
/** Author Rinzler (Encom)
/****/

import javax.xml.bind.annotation.XmlEnum;

@XmlEnum
public enum QuestTargetType
{
	NONE,
	AREA,
	FORCE,
	UNION
}