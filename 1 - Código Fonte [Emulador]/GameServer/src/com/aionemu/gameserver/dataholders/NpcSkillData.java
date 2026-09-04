package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.model.templates.npcskill.NpcSkillTemplates;

import gnu.trove.map.hash.TIntObjectHashMap;
import org.slf4j.LoggerFactory;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import java.util.*;

@XmlRootElement(name = "npc_skill_templates")
@XmlAccessorType(XmlAccessType.FIELD)
public class NpcSkillData
{
	@XmlElement(name = "npcskills")
	private List<NpcSkillTemplates> npcSkills;
	
	private TIntObjectHashMap<NpcSkillTemplates> npcSkillData = new TIntObjectHashMap<NpcSkillTemplates>();
	
	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (NpcSkillTemplates npcSkill : npcSkills) {
			npcSkillData.put(npcSkill.getNpcId(), npcSkill);
			if (npcSkill.getNpcSkills() == null) {
				LoggerFactory.getLogger(NpcSkillData.class).error("1 Npc has 0 skills in list!!!" + " id : " + npcSkill.getNpcId());
			}
		}
	}
	
	public int size() {
		return npcSkillData.size();
	}
	
	public NpcSkillTemplates getNpcSkillList(int id) {
		return npcSkillData.get(id);
	}
}