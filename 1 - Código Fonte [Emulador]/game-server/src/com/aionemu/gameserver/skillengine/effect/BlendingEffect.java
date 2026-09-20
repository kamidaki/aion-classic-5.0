package com.aionemu.gameserver.skillengine.effect;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Implementa as duas formas de Blending descritas pelos dados oficiais 5.0:
 * notas musicais do Luminess e acúmulo compartilhado entre graduações de uma skill.
 *
 * No modo de notas:
 * 1. Alvo: mantém os acúmulos (carvedSignet) de cada nota debuff.
 * 2. Jogador: mantém o BlendingState (sequência de notas utilizadas).
 * 3. Expiração: quando o efeito no alvo termina por tempo ou morte, BlendingState é resetado.
 * 4. Resolução de combo: remove os efeitos de notas do alvo antes de aplicar o finalizador.
 *
 * @author Antigravity
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "BlendingEffect")
public class BlendingEffect extends EffectTemplate {

	@XmlAttribute(name = "note")
	protected String note;
	@XmlAttribute(name = "stack_level")
	private int stackLevel;
	@XmlAttribute(name = "skill_id")
	private int skillId;
	@XmlAttribute(name = "source_skills")
	private String sourceSkills;

	@Override
	public void applyEffect(Effect effect) {
		Creature target = effect.getEffected();
		if (isStackBlending()) {
			if (effect.getCarvedSignet() >= stackLevel && target != null && !target.getLifeStats().isDead()) {
				var skill = SkillEngine.getInstance().getSkill(effect.getEffector(), skillId, 1, target);
				if (skill != null)
					skill.useWithoutPropSkill();
			}
			return;
		}
		int targetLiStacks = 0;

		// 1. Gerenciar acúmulos (carvedSignet) no efeito aplicado ao alvo
		if (target != null) {
			if (effect.getCarvedSignet() <= 0) {
				String currentStack = effect.getStack();
				String stackPrefix = getStackPrefix(currentStack);
				int count = 1;

				if (stackPrefix != null) {
					for (Effect active : target.getEffectController().getAbnormalEffects()) {
						if (active != effect && active.getStack() != null && active.getStack().startsWith(stackPrefix)) {
							count = active.getCarvedSignet() + 1;
							break;
						}
					}
				}

				if ("E".equals(note)) {
					count = Math.min(15, count);
				}
				effect.setCarvedSignet(count);
			}

			// Verificar quantidade de Li acumulados no alvo para o combo Do
			for (Effect active : target.getEffectController().getAbnormalEffects()) {
				if (active.getStack() != null && active.getStack().startsWith("LU_BLENDE")) {
					targetLiStacks = Math.max(targetLiStacks, active.getCarvedSignet());
				}
			}
			if ("E".equals(note)) {
				targetLiStacks = Math.max(targetLiStacks, effect.getCarvedSignet());
			}
		}

		// 2. Registrar nota no BlendingState do jogador e resolver combo
		if (effect.getEffector() instanceof Player player) {
			if (player.getPlayerClass() != com.aionemu.gameserver.model.PlayerClass.LUMINESS) {
				return;
			}
			BlendingNote blendingNote = BlendingNote.fromString(note);
			if (blendingNote != null) {
				player.getBlendingState().recordNote(blendingNote);
				Integer comboSkillId = player.getBlendingState().resolveCombo(targetLiStacks);
				if (comboSkillId != null) {
					player.getBlendingState().clear();
					if (target != null && !target.getLifeStats().isDead()) {
						// 3. Remover efeitos residuais das notas antes de disparar o finalizador oficial
						target.getEffectController().removeBlendingNoteEffects();
						SkillEngine.getInstance().getSkill(player, comboSkillId, 1, target).useWithoutPropSkill();
					}
				}
			}
		}
	}

	@Override
	public void endEffect(Effect effect) {
		if (isStackBlending())
			return;
		if (effect.getEffector() instanceof Player player) {
			// Reseta o BlendingState quando o efeito no alvo termina por expiração de tempo ou morte do alvo
			if (effect.isEndedByTime() || effect.getEffected() == null || effect.getEffected().getLifeStats().isDead()) {
				player.getBlendingState().clear();
			}
		}
	}

	@Override
	public void calculate(Effect effect) {
		effect.addSuccessEffect(this);

		Creature target = effect.getEffected();
		if (isStackBlending()) {
			int count = 1;
			if (target != null) {
				for (Effect active : target.getEffectController().getAbnormalEffects()) {
					if (active != effect && isSourceSkill(active.getSkillId())) {
						count = Math.min(stackLevel, Math.max(1, active.getCarvedSignet()) + 1);
						break;
					}
				}
			}
			effect.setCarvedSignet(count);
			return;
		}
		if (target != null) {
			String currentStack = effect.getStack();
			String stackPrefix = getStackPrefix(currentStack);
			int count = 1;

			if (stackPrefix != null) {
				for (Effect active : target.getEffectController().getAbnormalEffects()) {
					if (active != effect && active.getStack() != null && active.getStack().startsWith(stackPrefix)) {
						count = active.getCarvedSignet() + 1;
						break;
					}
				}
			}

			if ("E".equals(note)) {
				count = Math.min(15, count);
			}
			effect.setCarvedSignet(count);
		}
	}

	public String getNote() {
		return note;
	}

	private boolean isStackBlending() {
		return stackLevel > 0 && skillId > 0 && sourceSkills != null;
	}

	private boolean isSourceSkill(int activeSkillId) {
		for (String sourceSkill : sourceSkills.split(" ")) {
			if (!sourceSkill.isEmpty() && Integer.parseInt(sourceSkill) == activeSkillId)
				return true;
		}
		return false;
	}

	private static String getStackPrefix(String stack) {
		if (stack == null) {
			return null;
		}
		int idx = stack.lastIndexOf('_');
		return idx > 0 ? stack.substring(0, idx) : stack;
	}
}
