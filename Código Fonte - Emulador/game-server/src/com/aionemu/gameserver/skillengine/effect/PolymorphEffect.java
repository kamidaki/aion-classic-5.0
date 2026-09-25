package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.TransformType;

/**
 * So a transformacao em corpo de NPC (type NONE, reserved8 "None" no client_skills: Q_Polymorph_Drakan_01, EttinPolymorph...) assume a tribo
 * do NPC. As de tipo PC (candies, deuses, apostolos) mantem a do personagem: no candy de panda marinho (captura outros2 de 2026-09-22) o
 * oficial reenviou o S_CHANGE_FLAG de 40 NPCs e cada um ficou com o tipo que tinha no S_PUT_NPC.
 *
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "PolymorphEffect")
public class PolymorphEffect extends TransformEffect {

	@Override
	public void startEffect(Effect effect) {
		super.startEffect(effect);
		if (model > 0 && type == TransformType.NONE) {
			Creature effected = effect.getEffected();
			NpcTemplate template = DataManager.NPC_DATA.getNpcTemplate(model);
			if (template != null)
				effected.getTransformModel().setTribe(template.getTribe());
		}
	}

	@Override
	public void endEffect(Effect effect) {
		super.endEffect(effect);
		effect.getEffected().getTransformModel().setTribe(null);
	}
}
