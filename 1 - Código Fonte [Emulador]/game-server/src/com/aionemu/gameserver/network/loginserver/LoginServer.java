package com.aionemu.gameserver.network.loginserver;

import java.io.IOException;
import java.net.SocketException;
import java.nio.channels.SelectionKey;
import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.network.Dispatcher;
import com.aionemu.commons.network.NioServer;
import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.configs.main.SecurityConfig;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.AccountTime;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.network.BannedMacManager;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.serverpackets.SM_L2AUTH_LOGIN_CHECK;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NPSHOP_GOODS_COUNT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_REPLY_NP_AUTH_TOKEN;
import com.aionemu.gameserver.network.aion.serverpackets.SM_REPLY_NP_LOGIN_GAMESVR;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RECONNECT_KEY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.S_READY_ENTER_WORLD;
import com.aionemu.gameserver.network.loginserver.LoginServerConnection.State;
import com.aionemu.gameserver.network.loginserver.serverpackets.*;
import com.aionemu.gameserver.services.AccountService;
import com.aionemu.gameserver.services.ban.HDDBanService;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;

/**
 * @author Lost Academy Team & Durak
 */
public class LoginServer {

	private static final Logger log = LoggerFactory.getLogger(LoginServer.class);

	private final Map<Integer, LoginRequest> loginRequests = new ConcurrentHashMap<>();
	private final Map<Integer, AionConnection> loggedInAccounts = new ConcurrentHashMap<>();
	private LoginServerConnection lsCon = null;
	private NioServer nioServer = null;
	private int gameServerCount = 1;

	public static LoginServer getInstance() {
		return SingletonHolder.instance;
	}

	/**
	 * Prevent instantiation.
	 */
	private LoginServer() {
	}

	public void connect(NioServer nioServer) {
		if (lsCon != null)
			throw new IllegalStateException("Login server is already connected.");

		try {
			this.nioServer = nioServer;
			SocketChannel sc = SocketChannel.open(NetworkConfig.LOGIN_ADDRESS);
			sc.configureBlocking(false);
			Dispatcher d = nioServer.getReadWriteDispatcher();
			lsCon = new LoginServerConnection(sc, d);
			d.register(sc, SelectionKey.OP_READ, lsCon);
			lsCon.initialized();
		} catch (IOException e) {
			lsCon = null;
			int delay;
			if (e instanceof SocketException) {
				delay = 10;
				log.info("Could not connect to login server at " + NetworkConfig.LOGIN_ADDRESS + ", trying again in " + delay + "s");
			} else {
				delay = 60;
				log.error("Could not connect to login server at " + NetworkConfig.LOGIN_ADDRESS + ", trying again in " + delay + "s", e);
			}
			ThreadPoolManager.getInstance().schedule(() -> connect(nioServer), delay * 1000);
		}
	}

	/**
	 * When disconnecting we have to close all pending login requests to notify their clients.
	 */
	public void disconnect() {
		if (lsCon != null) {
			lsCon.close();
			lsCon = null;
		}
		for (LoginRequest loginRequest : loginRequests.values())
			loginRequest.connection.close();
		loginRequests.clear();
	}

	public void reconnect() {
		if (lsCon == null)
			return;
		int delay = lsCon.getState() == State.AUTHED ? 5 : 15;
		disconnect();
		log.info("Reconnecting to login server in " + delay + "s...");
		ThreadPoolManager.getInstance().schedule(() -> connect(nioServer), delay * 1000);
	}

	public boolean isUp() {
		return lsCon != null && lsCon.getState() == State.AUTHED;
	}

	/**
	 * Notify that client is disconnected - we must clear waiting request to LoginServer if any to prevent leaks. Also notify LoginServer that this
	 * account is no longer on GameServer side.
	 */
	public void onDisconnect(AionConnection connection) {
		loginRequests.values().removeIf(r -> r.connection == connection);
		if (connection.getAccount() != null) {
			int accId = connection.getAccount().getId();
			loggedInAccounts.remove(accId);
			AccountService.invalidateCache(accId);
			sendPacket(new SM_ACCOUNT_DISCONNECTED(accId));
		}
	}

	public void setGameServerCount(int gameServerCount) {
		this.gameServerCount = gameServerCount;
	}

	public int getGameServerCount() {
		return gameServerCount;
	}

	public void registerLoginRequest(int accountId, AionConnection client, int loginOk, int playOk1, int playOk2) {
		LoginRequest req = new LoginRequest(client, new SM_ACCOUNT_AUTH(accountId, loginOk, playOk1, playOk2));
		loginRequests.put(accountId, req);
		if (isUp())
			lsCon.sendPacket(req.lsAuthResponse);
		else
			client.close(new SM_L2AUTH_LOGIN_CHECK(false, null)); // disconnect this client since authentication will not happen
	}

	/**
	 * Starts authentication procedure of this client - LoginServer will send response with information about account name if authentication is ok.
	 */
	public void authenticateClient(AionConnection client) {
		if (!isUp())
			client.close(new SM_L2AUTH_LOGIN_CHECK(false, null)); // disconnect this client since authentication will not happen
	}

	/**
	 * This method is called by CM_ACCOUNT_AUTH_RESPONSE LoginServer packets to notify GameServer about results of client authentication.
	 */
	public void accountAuthenticationResponse(int accountId, String accountName, boolean result, long creationDate, AccountTime accountTime,
		byte accessLevel, byte membership, String allowedHddSerial) {
		LoginRequest loginRequest = loginRequests.remove(accountId);
		if (loginRequest == null)
			return;

		AionConnection client = loginRequest.connection;
		if (!result || !validateMacAndHddSerial(client, allowedHddSerial)) {
			client.close(new SM_L2AUTH_LOGIN_CHECK(false, accountName)); // LS sends no accName when result is false
			sendPacket(new SM_ACCOUNT_DISCONNECTED(accountId)); // disconnect manually from login server because account isn't attached to connection yet
			return;
		}
		Account account = AccountService.getAccount(accountId, accountName, creationDate, accountTime, accessLevel, membership, allowedHddSerial);
		if (SecurityConfig.HDD_SERIAL_LOCK_UNLOCKED_ACCOUNTS && account.getAllowedHddSerial().isEmpty() && !client.getHddSerial().isEmpty()) {
			account.setAllowedHddSerial(client.getHddSerial());
			sendPacket(new SM_CHANGE_ALLOWED_HDD_SERIAL(account));
		}
		kickOnlineCharacters(account);
		client.setAccount(account);
		client.setState(AionConnection.State.AUTHED);
		loggedInAccounts.put(accountId, client);
		log.info(account + " authed with MAC: " + client.getMacAddress() + " and HDD serial: " + client.getHddSerial());

		// Envio dos pacotes de autenticacao NP (NetPasskey) e autorizacao de entrada no mundo (Classic 5.0)
		// Conforme captura oficial Wireshark (01_Login_World_Elyos):
		// 1) S_REPLY_NP_LOGIN_GAMESVR (x2)
		// 2) S_NPSHOP_GOODS_COUNT (0)
		// 3) S_READY_ENTER_WORLD (0, code)
		// 4) S_REPLY_NP_AUTH_TOKEN (token Gameforge Classic 5.0)
		// 5) S_L2AUTH_LOGIN_CHECK
		client.sendPacket(new SM_REPLY_NP_LOGIN_GAMESVR());
		client.sendPacket(new SM_REPLY_NP_LOGIN_GAMESVR());
		client.sendPacket(new SM_NPSHOP_GOODS_COUNT(0));
		int code = Rnd.get(300000000, 400000000);
		client.sendPacket(new S_READY_ENTER_WORLD(0, code));
		client.sendPacket(new SM_REPLY_NP_AUTH_TOKEN("014D6A677A526B55344E54517452446730524330304E7A41304C5549354D546374516A41304E6B517A4D6A52434E454A424F6B4E445244597752454D774C5549344F5555744E4445784F5331434E5546464C546B79525468464E545132525459324E41413D0038423535373337342D313837322D343742432D393833442D3735383230373132313441360061696F6E67666300140c03"));
		client.sendPacket(new SM_REPLY_NP_AUTH_TOKEN("014D5546474D6A6378526A51744E7A5644515330304D3059304C554A4551554D744F4446464E6A67794D455A45526B597A4F6A45354E454D33516B4D774C5551344E7A59744E44644451533142515455324C546C474D4441794E7A59304E5468474F41413D0036374443393030452D333544422D423942302D423133442D4333344641343846394538340061696F6E6E637700FA0102"));
		client.sendPacket(new SM_L2AUTH_LOGIN_CHECK(true, accountName));
		sendPacket(new SM_ACCOUNT_CONNECTION_INFO(account.getId(), System.currentTimeMillis(), client.getIP(), client.getMacAddress(), client.getHddSerial()));
	}

	private boolean validateMacAndHddSerial(AionConnection client, String allowedHddSerial) {
		String mac = client.getMacAddress();
		if (mac != null && !mac.isEmpty() && BannedMacManager.getInstance().isBanned(mac)) {
			log.info(client + " was kicked due to mac ban");
			return false;
		} else if (client.getHddSerial() != null && !client.getHddSerial().isEmpty() && HDDBanService.getInstance().isBanned(client.getHddSerial())) {
			log.info(client + " was kicked because hdd serial " + client.getHddSerial() + " is banned");
			return false;
		} else if (SecurityConfig.HDD_SERIAL_LOCK_ENABLE && allowedHddSerial != null && !allowedHddSerial.isEmpty() && client.getHddSerial() != null && !allowedHddSerial.equals(client.getHddSerial())) {
			log.info(client + " was kicked due to hdd serial mismatch. Expected " + allowedHddSerial + " but client connected with " + client.getHddSerial());
			return false;
		}
		return true;
	}

	private void kickOnlineCharacters(Account account) {
		for (PlayerAccountData accountData : account) {
			PlayerCommonData pcd = accountData.getPlayerCommonData();
			if (pcd.isOnline()) {
				Player player = World.getInstance().getPlayer(pcd.getPlayerObjId());
				if (player != null && player.getClientConnection() != null) {
					player.getClientConnection().close(SM_SYSTEM_MESSAGE.STR_KICK_ANOTHER_USER_TRY_LOGIN()); // kick
				}
			}
		}
	}

	/**
	 * Starts reconnection to LoginServer procedure. LoginServer in response will send reconnection key.
	 */
	public void requestAuthReconnection(int accountId, AionConnection client) {
		if (isUp() && client.equals(loggedInAccounts.get(accountId)))
			lsCon.sendPacket(new SM_ACCOUNT_RECONNECT_KEY(client.getAccount().getId()));
		else
			client.close(/* closePacket */);
	}

	/**
	 * This method is called by CM_ACCOUNT_RECONNECT_KEY LoginServer packets to give GameServer reconnection key for client that was requesting
	 * reconnection.
	 */
	public void authReconnectionResponse(int accountId, int reconnectKey) {
		AionConnection client = loggedInAccounts.get(accountId);
		if (client == null)
			return;
		client.close(new SM_RECONNECT_KEY(reconnectKey));
	}

	/**
	 * This method is called by CM_REQUEST_KICK_ACCOUNT LoginServer packets to request GameServer to disconnect client with given account id.
	 */
	public void kickAccount(int accountId, boolean notifyDoubleLogin) {
		AionConnection client = loggedInAccounts.get(accountId);
		if (client != null) {
			log.info("Kicking account ID " + accountId + " by LS request.");
			client.close(notifyDoubleLogin ? SM_SYSTEM_MESSAGE.STR_KICK_ANOTHER_USER_TRY_LOGIN() : null);
		}
	}

	public void sendLoggedInAccounts() {
		sendPacket(new SM_ACCOUNT_LIST(new ArrayList<>(loggedInAccounts.values())));
	}

	public void sendLsControlPacket(int type, int param, Player player, Player admin) {
		sendPacket(new SM_LS_CONTROL(type, param, player, admin));
	}

	public AionConnection accountUpdate(int accountId, int type, byte param) {
		AionConnection client = loggedInAccounts.get(accountId);
		if (client != null) {
			Account account = client.getAccount();
			if (type == 1)
				account.setAccessLevel(param);
			else if (type == 2)
				account.setMembership(param);
			return client;
		}
		return null;
	}

	public void sendBanPacket(byte type, int accountId, String ip, int time, int adminObjId) {
		sendPacket(new SM_BAN(type, accountId, ip, time, adminObjId));
	}

	public boolean sendPacket(LsServerPacket pk) {
		if (isUp()) {
			lsCon.sendPacket(pk);
			return true;
		} else
			return false;
	}

	private static class SingletonHolder {

		protected static final LoginServer instance = new LoginServer();
	}

	private record LoginRequest(AionConnection connection, SM_ACCOUNT_AUTH lsAuthResponse) {}
}
