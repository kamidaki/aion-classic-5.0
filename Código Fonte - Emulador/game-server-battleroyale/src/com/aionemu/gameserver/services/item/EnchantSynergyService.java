package com.aionemu.gameserver.services.item;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.calc.StatOwner;
import com.aionemu.gameserver.model.templates.item.EnchantSynergyLevel;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ENCHANT_SYNERGY;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Sinergia de encantamento do Classic 5.0 ("Current Synergy Level", client_accumulated_enchant_effect.xml).
 * <p>
 * O nível é a soma dos encantamentos dos itens equipados com accumulated_enchant_effect (grau Único ou acima,
 * STR_EQUIP_ENCHANT_BONUS_CONDITION_DESC). O cliente só o mostra (STR_EQUIP_ENCHANT_BONUS_ALL) depois do S 0x173 [D soma]; sem ele fica
 * N/A. O servidor aplica o bônus do maior nível com enchant_sum <= soma: os atributos mais a activation_skill (drop e AP, 60+). Nenhuma
 * captura tem as skills 3989-3991/4218-4221 na lista de skills, por isso a skill entra como efeito passivo, sem S_ADD_SKILL.
 */
public final class EnchantSynergyService {

	private static final Logger log = LoggerFactory.getLogger(EnchantSynergyService.class);

	private static final Map<Integer, Synergy> applied = new ConcurrentHashMap<>();
	/** última soma enviada no S 0x173, por jogador */
	private static final Map<Integer, Integer> sentSum = new ConcurrentHashMap<>();

	/** dono dos atributos do nível aplicado a um jogador */
	private static final class Synergy implements StatOwner {

		private final EnchantSynergyLevel level;

		private Synergy(EnchantSynergyLevel level) {
			this.level = level;
		}
	}

	private EnchantSynergyService() {
	}

	public static int getEnchantSum(Player player) {
		int sum = 0;
		for (Item item : player.getEquipment().getEquippedItemsWithoutStigma())
			if (DataManager.ENCHANT_SYNERGY_DATA.isSynergyItem(item.getItemId()))
				sum += item.getEnchantLevel();
		return sum;
	}

	/**
	 * Recalcula depois de equipar, desequipar ou mudar o encantamento de um item equipado; só troca o bônus quando o nível muda.
	 */
	public static void recalculate(Player player) {
		int enchantSum = getEnchantSum(player);
		if (player.isSpawned())
			sendLevel(player, enchantSum);
		EnchantSynergyLevel level = DataManager.ENCHANT_SYNERGY_DATA.getLevel(enchantSum);
		Synergy current = applied.get(player.getObjectId());
		if (current != null && current.level == level)
			return;
		if (current != null)
			remove(player, current);
		if (level == null) {
			applied.remove(player.getObjectId());
			return;
		}
		Synergy synergy = new Synergy(level);
		applied.put(player.getObjectId(), synergy);
		player.getGameStats().addEffect(synergy, level.getModifiers());
		if (level.getSkillId() != 0 && (current == null || current.level.getSkillId() != level.getSkillId())) {
			SkillTemplate skill = DataManager.SKILL_DATA.getSkillTemplate(level.getSkillId());
			if (skill != null && player.getEffectController() != null)
				SkillEngine.getInstance().applyEffectDirectly(skill, 1, player, player);
		}
		log.debug("Sinergia de {}: nível {}", player.getName(), level.getSum());
	}

	/**
	 * Entrada no mundo, depois da lista de skills: o oficial manda o 0x173 já com a soma (item a item; aqui só o total).
	 */
	public static void onEnterWorld(Player player) {
		sentSum.remove(player.getObjectId());
		sendLevel(player, getEnchantSum(player));
	}

	public static void onLogout(Player player) {
		applied.remove(player.getObjectId());
		sentSum.remove(player.getObjectId());
	}

	private static void sendLevel(Player player, int enchantSum) {
		Integer previous = sentSum.put(player.getObjectId(), enchantSum);
		if (previous == null || previous != enchantSum)
			PacketSendUtility.sendPacket(player, new SM_ENCHANT_SYNERGY(enchantSum));
	}

	private static void remove(Player player, Synergy synergy) {
		player.getGameStats().endEffect(synergy);
		int skillId = synergy.level.getSkillId();
		EnchantSynergyLevel next = DataManager.ENCHANT_SYNERGY_DATA.getLevel(getEnchantSum(player));
		if (skillId != 0 && (next == null || next.getSkillId() != skillId) && player.getEffectController() != null)
			player.getEffectController().removeEffect(skillId);
	}
}
