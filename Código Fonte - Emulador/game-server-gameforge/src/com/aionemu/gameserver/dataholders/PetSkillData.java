package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;

import com.aionemu.gameserver.model.templates.petskill.PetSkillTemplate;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "pet_skill_templates")
@XmlAccessorType(XmlAccessType.FIELD)
public class PetSkillData {

	@XmlElement(name = "pet_skill")
	private List<PetSkillTemplate> petSkills;

	@XmlTransient
	private final Map<Integer, Map<Integer, Integer>> petSkillData = new HashMap<>();
	@XmlTransient
	private final Map<Integer, List<Integer>> petSkillsMap = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (PetSkillTemplate petSkill : petSkills) {
			petSkillData.computeIfAbsent(petSkill.getOrderSkill(), k -> new HashMap<>()).put(petSkill.getPetId(), petSkill.getSkillId());
			petSkillsMap.computeIfAbsent(petSkill.getPetId(), k -> new ArrayList<>()).add(petSkill.getSkillId());
		}
		petSkills = null;
	}

	public int size() {
		return petSkillData.size();
	}

	public boolean isPetOrderSkill(int orderSkill) {
		if (!petSkillData.containsKey(orderSkill)) {
			return false;
		}
		com.aionemu.gameserver.skillengine.model.SkillTemplate template = DataManager.SKILL_DATA != null ? DataManager.SKILL_DATA.getSkillTemplate(orderSkill) : null;
		if (template != null && !template.getStack().startsWith("EL_ORDER_")) {
			return false;
		}
		return true;
	}

	/**
	 * @return id da skill que o pet usa para a ordem, 0 quando o par ordem/pet não existe
	 */
	public int getPetOrderSkill(int orderSkill, int petNpcId) {
		Map<Integer, Integer> skillsByPet = petSkillData.get(orderSkill);
		Integer skillId = skillsByPet == null ? null : skillsByPet.get(petNpcId);
		return skillId == null ? 0 : skillId;
	}

	public boolean petHasSkill(int petNpcId, int skillId) {
		List<Integer> skills = petSkillsMap.get(petNpcId);
		return skills != null && skills.contains(skillId);
	}
}
