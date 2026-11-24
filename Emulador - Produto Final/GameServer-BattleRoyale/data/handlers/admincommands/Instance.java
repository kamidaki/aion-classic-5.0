package admincommands;

import static com.aionemu.gameserver.configs.main.AutoGroupConfig.*;

import com.aionemu.gameserver.model.autogroup.AutoGroupType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.instance.PeriodicInstanceManager;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * @author Lost Academy Team & Durak
 */
public class Instance extends AdminCommand {

	public Instance() {
		super("instance", "Activates or deactivates registration for pvp instances.");

		// @formatter:off
			setSyntaxInfo(
				"<open|close> dredgion - Opens/closes registration for Baranath Dredgion",
				"<open|close> chantra - Opens/closes registration for Chantra Dredgion",
				"<open|close> tiarkh - Opens/closes registration for Tiarkh Testing Lab",
				"<open|close> dranium - Opens/closes registration for Dranium Battlefield",
				"<open|close> sonsara - Opens/closes registration for Sonsara"
			);
			// @formatter:on
	}

	@Override
	public void execute(Player admin, String... params) {
		if (params.length < 2) {
			sendInfo(admin);
			return;
		}

		if ("open".equalsIgnoreCase(params[0])) {
			openRegistration(admin, params[1]);
		} else if ("close".equalsIgnoreCase(params[0])) {
			closeRegistration(admin, params[1]);
		} else {
			sendInfo(admin);
		}
	}

	private void openRegistration(Player admin, String instanceName) {
		SM_SYSTEM_MESSAGE openingMsg;
		int maskId;
		long registrationPeriod;

		switch (instanceName.toLowerCase()) {
			case "dredgion" -> {
				openingMsg = SM_SYSTEM_MESSAGE.STR_MSG_INSTANCE_OPEN_IDAB1_DREADGION();
				maskId = 1;
				registrationPeriod = DREDGION_REGISTRATION_PERIOD;
			}
			case "chantra" -> {
				openingMsg = SM_SYSTEM_MESSAGE.STR_MSG_INSTANCE_OPEN_IDDREADGION_02();
				maskId = 2;
				registrationPeriod = CHANTRA_REGISTRATION_PERIOD;
			}
			case "tiarkh" -> {
				openingMsg = null;
				maskId = 33;
				registrationPeriod = TIARKH_LAB_REGISTRATION_PERIOD;
			}
			case "dranium" -> {
				openingMsg = null;
				maskId = 51;
				registrationPeriod = DRANIUM_BATTLEFIELD_REGISTRATION_PERIOD;
			}
			case "sonsara" -> {
				openingMsg = null;
				maskId = 52;
				registrationPeriod = SONSARA_REGISTRATION_PERIOD;
			}
			default -> {
				openingMsg = null;
				maskId = 0;
				registrationPeriod = 0;
			}
		}
		if (maskId != 0) {
			if (PeriodicInstanceManager.getInstance().openRegistration(openingMsg, maskId, registrationPeriod))
				sendInfo(admin, "Registration for " + AutoGroupType.getAGTByMaskId(maskId) + " is now open.");
			else
				sendInfo(admin, "Registration for " + AutoGroupType.getAGTByMaskId(maskId) + " is already open.");
		} else {
			sendInfo(admin, "No instance found for " + instanceName);
		}
	}

	private void closeRegistration(Player admin, String instanceName) {
		int maskId;

		switch (instanceName.toLowerCase()) {
			case "dredgion" -> maskId = 1;
			case "chantra" -> maskId = 2;
			case "tiarkh" -> maskId = 33;
			case "dranium" -> maskId = 51;
			case "sonsara" -> maskId = 52;
			default -> maskId = 0;
		}

		if (maskId != 0) {
			if (PeriodicInstanceManager.getInstance().closeRegistration(maskId))
				sendInfo(admin, "Registration for " + AutoGroupType.getAGTByMaskId(maskId) + " is now closed.");
			else
				sendInfo(admin, "Registration for " + AutoGroupType.getAGTByMaskId(maskId) + " is not open.");
		} else {
			sendInfo(admin, "No instance found for " + instanceName);
		}
	}

}
