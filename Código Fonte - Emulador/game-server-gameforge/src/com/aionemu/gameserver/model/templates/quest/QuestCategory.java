package com.aionemu.gameserver.model.templates.quest;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlType(name = "QuestCategory")
@XmlEnum
public enum QuestCategory {
	QUEST,
	EVENT,
	MISSION,
	SIGNIFICANT,
	IMPORTANT,
	NON_COUNT,
	SEEN_MARKER,
	TASK,
	FACTION,
	CHALLENGE_TASK,
	PUBLIC,
	LEGION,
	PRIMARY;
}
