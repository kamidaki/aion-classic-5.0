package admincommands;

import java.util.Collection;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.siege.CampLocation;
import com.aionemu.gameserver.model.siege.SiegeRace;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.services.CampWarService;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * Testa o camp war das torres de Tiamaranta Mesa sem esperar os 300/600/900 s de protecao.
 *
 * @author Lost Academy Team & Durak
 */
public class Camp extends AdminCommand {

	public Camp() {
		super("camp", "Estado das torres de Tiamaranta: //camp | //camp <id> <elyos|asmodians|balaur> | //camp <id> vuln");
	}

	@Override
	public void execute(Player admin, String... params) {
		Collection<CampLocation> camps = CampWarService.getInstance().getCamps();
		if (camps.isEmpty()) {
			sendInfo(admin, "Nenhuma torre carregada (sieges desligadas no config?).");
			return;
		}
		if (params.length == 0) {
			for (CampLocation camp : camps) {
				int falta = camp.getRemainingPhaseSeconds();
				sendInfo(admin, String.format("%d: %s %s%s%s", camp.getLocationId(), camp.getRace(),
					camp.isVulnerable() ? "vulneravel" : "protegida", camp.isStatic() ? " (desligada)" : "",
					falta > 0 ? " - faltam " + falta + "s" : ""));
			}
			return;
		}
		if (params.length < 2) {
			sendInfo(admin, "Uso: //camp | //camp <id> <elyos|asmodians|balaur> | //camp <id> vuln");
			return;
		}

		CampLocation camp;
		try {
			camp = CampWarService.getInstance().getCamp(Integer.parseInt(params[0]));
		} catch (NumberFormatException e) {
			sendInfo(admin, "Id invalido: " + params[0]);
			return;
		}
		if (camp == null) {
			sendInfo(admin, "Nao existe torre com o id " + params[0] + ". Use //camp para listar.");
			return;
		}

		if (camp.isStatic()) {
			sendInfo(admin, "Torre " + camp.getLocationId() + " e de dono fixo (" + camp.getRace() + ") e nao entra no camp war.");
			return;
		}
		if (params[1].equalsIgnoreCase("vuln")) {
			CampWarService.getInstance().tornaVulneravel(camp);
			sendInfo(admin, "Torre " + camp.getLocationId() + " agora esta vulneravel (o boss nasceu).");
			return;
		}

		SiegeRace nova;
		try {
			nova = SiegeRace.valueOf(params[1].toUpperCase());
		} catch (IllegalArgumentException e) {
			sendInfo(admin, "Raca invalida: " + params[1] + " (elyos, asmodians ou balaur)");
			return;
		}
		Legion legion = nova == SiegeRace.BALAUR ? null : admin.getLegion();
		CampWarService.getInstance().captura(camp, nova, legion == null ? 0 : legion.getLegionId(),
			legion == null ? null : legion.getName());
		sendInfo(admin, "Torre " + camp.getLocationId() + " entregue a " + nova + "; a guarnicao troca em 1 s.");
	}
}
