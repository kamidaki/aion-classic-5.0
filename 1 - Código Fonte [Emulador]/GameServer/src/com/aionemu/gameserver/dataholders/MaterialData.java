package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.model.templates.materials.MaterialSkill;
import com.aionemu.gameserver.model.templates.materials.MaterialTemplate;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;
import java.util.*;





@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "", propOrder = { "materialTemplates" })
@XmlRootElement(name = "material_templates")
public class MaterialData {

	@XmlElement(name = "material")
	protected List<MaterialTemplate> materialTemplates;

	@XmlTransient
	Map<Integer, MaterialTemplate> materialsById = new HashMap<Integer, MaterialTemplate>();

	@XmlTransient
	Set<Integer> skillIds = new HashSet<Integer>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (materialTemplates == null)
			return;

		for (MaterialTemplate template : materialTemplates) {
			materialsById.put(template.getId(), template);
			if (template.getSkills() != null) {
				for (MaterialSkill skill : template.getSkills()) {
					skillIds.add(skill.getId());
				}
			}
		}

		materialTemplates.clear();
		materialTemplates = null;
	}

	public MaterialTemplate getTemplate(int materialId) {
		return materialsById.get(materialId);
	}

	public boolean isMaterialSkill(int skillId) {
		return skillIds.contains(skillId);
	}

	public int size() {
		return materialsById.size();
	}

}
