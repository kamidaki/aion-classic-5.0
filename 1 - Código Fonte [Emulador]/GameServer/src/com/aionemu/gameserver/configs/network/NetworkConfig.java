package com.aionemu.gameserver.configs.network;

import com.aionemu.commons.configuration.Property;

import java.net.InetSocketAddress;

public class NetworkConfig {

	/**
	 * Game Server port
	 */
	@Property(key = "gameserver.network.client.port", defaultValue = "7777")
	public static int GAME_PORT;

	/**
	 * Game Server bind ip
	 */
	@Property(key = "gameserver.network.client.host", defaultValue = "*")
	public static String GAME_BIND_ADDRESS;

	/**
	 * Max allowed online players
	 */
	@Property(key = "gameserver.network.client.maxplayers", defaultValue = "100")
	public static int MAX_ONLINE_PLAYERS;

	/**
	 * LoginServer address
	 */
	@Property(key = "gameserver.network.login.address", defaultValue = "localhost:9014")
	public static InetSocketAddress LOGIN_ADDRESS;

	/**
	 * ChatServer address
	 */
	@Property(key = "gameserver.network.chat.address", defaultValue = "localhost:9021")
	public static InetSocketAddress CHAT_ADDRESS;

	/**
	 * Password for this GameServer ID for authentication at ChatServer.
	 */
	@Property(key = "gameserver.network.chat.password", defaultValue = "")
	public static String CHAT_PASSWORD;

	/**
	 * GameServer id that this GameServer will request at LoginServer.
	 */
	@Property(key = "gameserver.network.login.gsid", defaultValue = "0")
	public static int GAMESERVER_ID;

	/**
	 * Password for this GameServer ID for authentication at LoginServer.
	 */
	@Property(key = "gameserver.network.login.password", defaultValue = "")
	public static String LOGIN_PASSWORD;

	/**
	 * Number of Threads dedicated to be doing io read & write.
	 * There is always 1 acceptor thread.
	 * If value is < 1 - acceptor thread will also handle read & write.
	 * If value is > 0 - there will be given amount of read & write threads
	 * + 1 acceptor thread.
	 */
	@Property(key = "gameserver.network.nio.threads", defaultValue = "1")
	public static int NIO_READ_WRITE_THREADS;

	/**
	 * Number of minimum threads that will be used to execute aion client packets.
	 */
	@Property(key = "gameserver.network.packet.processor.threads.min", defaultValue = "4")
	public static int PACKET_PROCESSOR_MIN_THREADS;

	/**
	 * Number of maximum threads that will be used to execute aion client packets. 
	 */
	@Property(key = "gameserver.network.packet.processor.threads.max", defaultValue = "4")
	public static int PACKET_PROCESSOR_MAX_THREADS;

	/**
	 * Threshold that will be used to decide when extra threads are not needed.
	 * (it doesn't have any effect if min threads == max threads)
	 */
	@Property(key = "gameserver.network.packet.processor.threshold.kill", defaultValue = "3")
	public static int PACKET_PROCESSOR_THREAD_KILL_THRESHOLD;

	/**
	 * Threshold that will be used to decide when extra threads should be spawned.
	 * (it doesn't have any effect if min threads == max threads)
	 */
	@Property(key = "gameserver.network.packet.processor.threshold.spawn", defaultValue = "50")
	public static int PACKET_PROCESSOR_THREAD_SPAWN_THRESHOLD;

	/**
	 * If unknown packets should be logged.
	 */
	@Property(key = "gameserver.network.display.unknownpackets", defaultValue = "false")
	public static boolean DISPLAY_UNKNOWNPACKETS;

	@Property(key = "gameserver.network.display.packets", defaultValue = "false")
	public static boolean DISPLAY_PACKETS;

	/**
	 * Rastreia todo pacote que entra e sai em `log/wiretrace.log`, para comparar a nossa
	 * sequencia com a das capturas oficiais. Diagnostico apenas -- custa uma linha por pacote.
	 */
	@Property(key = "gameserver.network.wiretrace", defaultValue = "false")
	public static boolean WIRE_TRACE;

	/**
	 * Diagnostico: reproduz na entrada no mundo os pacotes que a captura oficial traz e nos nao
	 * enviamos, com o corpo lido de `data/diagnostico/rajada_oficial.txt`. Desligado em producao.
	 */
	@Property(key = "gameserver.network.diagnostico.rajada", defaultValue = "false")
	public static boolean RAJADA_OFICIAL;

	/**
	 * Quantos bytes de payload o rastreador grava por pacote. 32 basta para identificar; para
	 * comparar campo a campo com a captura e preciso o corpo inteiro (use um valor alto, ex. 8192).
	 */
	@Property(key = "gameserver.network.wiretrace.bytes", defaultValue = "32")
	public static int WIRE_TRACE_BYTES;

	/**
	 * Diagnostico: opcodes S->C descartados enquanto o jogador nao fez spawn, separados por
	 * virgula (ex.: "0xBE,0x18"). Serve para conferir se a entrada no mundo trava por causa de
	 * algo que so nos enviamos. Vazio em producao.
	 */
	@Property(key = "gameserver.network.enterworld.filtro", defaultValue = "")
	public static String ENTER_WORLD_FILTER;

	@Property(key = "gameserver.network.flood.connections", defaultValue = "false")
	public static boolean ENABLE_FLOOD_CONNECTIONS;

	@Property(key = "gameserver.network.flood.tick", defaultValue = "1000")
	public static int Flood_Tick;
	
	@Property(key = "gameserver.network.flood.short.warn", defaultValue = "10")
	public static int Flood_SWARN;

	@Property(key = "gameserver.network.flood.short.reject", defaultValue = "20")
	public static int Flood_SReject;

	@Property(key = "gameserver.network.flood.short.tick", defaultValue = "10")
	public static int Flood_STick;
	
	@Property(key = "gameserver.network.flood.long.warn", defaultValue = "30")
	public static int Flood_LWARN;

	@Property(key = "gameserver.network.flood.long.reject", defaultValue = "60")
	public static int Flood_LReject;

	@Property(key = "gameserver.network.flood.long.tick", defaultValue = "60")
	public static int Flood_LTick;
}
