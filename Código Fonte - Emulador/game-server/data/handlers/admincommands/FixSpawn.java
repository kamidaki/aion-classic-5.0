package admincommands;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.locks.ReentrantLock;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.spawnengine.SpawnEngine;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.chathandlers.AdminCommand;

/**
 * Comando para administradores corrigirem NPCs flutuando e suas direcoes (heading).
 * Suporta execucoes via: //fixspawn, //fix, .fixspawn, .fix
 * Suporta variacao para corrigir apenas Heading: //fixspawn h, .fixspawn h
 * Salva a alteracao diretamente no arquivo XML de spawn original onde o NPC reside,
 * preservando 100% dos comentarios, quebras de linha e formatacao.
 *
 * @author Lost Academy Team & Antigravity
 */
public class FixSpawn extends AdminCommand {

	private static final Logger log = LoggerFactory.getLogger(FixSpawn.class);
	private static final ReentrantLock XML_LOCK = new ReentrantLock();

	public FixSpawn() {
		super("fixspawn", "Corrige altura (Z) e direcao (Heading) de NPCs flutuando.");

		setSyntaxInfo(
			" - Corrige altura (Z) e direcao (Heading) do NPC para o chao/NavMesh referenciado pelo jogador (preserva X e Y).",
			"h - Corrige apenas a direcao (Heading) do NPC para a do jogador (preserva X, Y e Z).",
			"player - Forca o Z exato do jogador sem ajuste de chao/NavMesh.",
			"geo - Corrige o Z usando estritamente o chao NavMesh/GeoEngine no X,Y do NPC."
		);
	}

	@Override
	public void execute(Player admin, String... params) {
		performFix(admin, params);
	}

	/**
	 * Logica central compartilhada entre FixSpawn, Fix, PlayerFixSpawn e PlayerFix.
	 */
	public static void performFix(Player admin, String... params) {
		if (admin == null || admin.getPosition() == null) {
			return;
		}

		boolean onlyHeading = false;
		boolean forcePlayerZ = false;
		boolean forceGeoZ = false;
		if (params != null && params.length > 0) {
			String arg = params[0].trim().toLowerCase();
			if (arg.equals("help") || arg.equals("?")) {
				PacketSendUtility.sendMessage(admin, "\u00a73[FixSpawn] Sintaxe:\n"
					+ "  //fixspawn (ou //fix / .fix / .fixspawn) -> Corrige Z (chao NavMesh/Geo no nivel do jogador) e Heading (preserva X e Y)\n"
					+ "  //fixspawn h (ou .fixspawn h) -> Corrige apenas Heading para o jogador (preserva X, Y e Z)\n"
					+ "  //fixspawn player -> Forca o Z exato do jogador (preserva X e Y)\n"
					+ "  //fixspawn geo -> Corrige o Z pelo NavMesh/GeoEngine relativo ao Z do NPC");
				return;
			} else if (arg.equals("h")) {
				onlyHeading = true;
			} else if (arg.equals("player") || arg.equals("p")) {
				forcePlayerZ = true;
			} else if (arg.equals("geo") || arg.equals("g")) {
				forceGeoZ = true;
			}
		}

		List<Npc> npcsToFix = new ArrayList<>();
		VisibleObject target = admin.getTarget();

		if (target != null && !target.equals(admin)) {
			if (target instanceof Npc npc) {
				if (npc.getSpawn() != null) {
					npcsToFix.add(npc);
				} else {
					PacketSendUtility.sendMessage(admin, "\u00a74[FixSpawn] O NPC selecionado nao possui template de spawn valido.");
					return;
				}
			} else {
				PacketSendUtility.sendPacket(admin, SM_SYSTEM_MESSAGE.STR_INVALID_TARGET());
				PacketSendUtility.sendMessage(admin, "\u00a74[FixSpawn] O alvo selecionado nao e um NPC.");
				return;
			}
		} else {
			// Sem target ou target no proprio admin: buscar NPCs em um raio horizontal 2D de 10 metros
			float adminX = admin.getX();
			float adminY = admin.getY();
			float maxRadius2D = 10.0f;

			admin.getPosition().getWorldMapInstance().forEachNpc(npc -> {
				if (npc != null && npc.isSpawned() && npc.getSpawn() != null) {
					float dx = npc.getX() - adminX;
					float dy = npc.getY() - adminY;
					float dist2D = (float) Math.hypot(dx, dy);
					if (dist2D <= maxRadius2D) {
						npcsToFix.add(npc);
					}
				}
			});

			if (npcsToFix.isEmpty()) {
				PacketSendUtility.sendMessage(admin, "\u00a74[FixSpawn] Nenhum NPC encontrado no raio horizontal de 10 metros.\n"
					+ "Posicione-se abaixo dos NPCs ou selecione um NPC como alvo.");
				return;
			}
		}

		int successCount = 0;
		for (Npc npc : npcsToFix) {
			SpawnTemplate spawn = npc.getSpawn();
			if (spawn == null) {
				continue;
			}

			int npcId = npc.getNpcId();
			int worldId = npc.getWorldId();
			float origX = spawn.getX();
			float origY = spawn.getY();
			float origZ = spawn.getZ();

			float newX = origX;
			float newY = origY;
			float newZ;
			if (onlyHeading) {
				newZ = origZ;
			} else if (forcePlayerZ) {
				newZ = admin.getZ();
			} else if (forceGeoZ) {
				newZ = SpawnEngine.resolveSpawnGroundZ(worldId, origX, origY, origZ, admin.getInstanceId());
			} else {
				float groundZ = SpawnEngine.resolveSpawnGroundZ(worldId, origX, origY, admin.getZ(), admin.getInstanceId());
				if (!Float.isNaN(groundZ) && Math.abs(groundZ - admin.getZ()) <= 4.0f) {
					newZ = groundZ;
				} else {
					newZ = admin.getZ();
				}
			}
			byte newH = admin.getHeading();

			// 1. Deletar do mundo o NPC antigo
			npc.getController().delete();

			// 2. Atualizar coordenadas no SpawnTemplate
			spawn.setX(newX);
			spawn.setY(newY);
			spawn.setZ(newZ);
			spawn.setHeading(newH);

			// 3. Respawnar o NPC nas novas coordenadas
			SpawnEngine.spawnObject(spawn, admin.getInstanceId());

			// 4. Atualizar cirurgicamente no arquivo XML original preservando comentarios
			String savedFileName = updateSpawnInXml(worldId, npcId, origX, origY, origZ, newZ, newH, onlyHeading);
			if (savedFileName != null) {
				successCount++;
				String msg = onlyHeading
					? "\u00a72[FixSpawn] NPC " + npc.getName() + " [ID: " + npcId + "] Heading atualizado para H=" + newH + ". Salvo em: " + savedFileName
					: "\u00a72[FixSpawn] NPC " + npc.getName() + " [ID: " + npcId + "] Altura Z e Heading atualizados (Z=" + String.format(Locale.US, "%.2f", newZ) + ", H=" + newH + "). Salvo em: " + savedFileName;
				PacketSendUtility.sendMessage(admin, msg);
			} else {
				PacketSendUtility.sendMessage(admin, "\u00a76[FixSpawn] NPC " + npc.getName() + " [ID: " + npcId + "] respawnado com sucesso, mas nao foi encontrado em nenhum XML de static_data/spawns.");
			}
		}

		if (npcsToFix.size() > 1) {
			PacketSendUtility.sendMessage(admin, "\u00a72[FixSpawn] Concluido: " + successCount + " de " + npcsToFix.size() + " NPCs foram corrigidos e salvos no XML.");
		}
	}

	/**
	 * Localiza o arquivo XML original onde o spot existe e atualiza seus atributos cirurgicamente.
	 */
	public static String updateSpawnInXml(int worldId, int npcId, float origX, float origY, float origZ, float newZ, byte newH, boolean onlyHeading) {
		XML_LOCK.lock();
		try {
			List<File> baseDirs = getSpawnsDirectories();
			String savedFileName = null;

			for (File spawnsDir : baseDirs) {
				if (!spawnsDir.exists() || !spawnsDir.isDirectory()) {
					continue;
				}

				File targetFile = findXmlFileForSpawn(spawnsDir, worldId, npcId, origX, origY, origZ);
				if (targetFile != null) {
					if (modifyXmlFile(targetFile, worldId, npcId, origX, origY, origZ, newZ, newH, onlyHeading)) {
						if (savedFileName == null) {
							savedFileName = targetFile.getName();
						}
					}
				}
			}
			return savedFileName;
		} finally {
			XML_LOCK.unlock();
		}
	}

	private static List<File> getSpawnsDirectories() {
		List<File> dirs = new ArrayList<>(7);
		addDirIfValid(dirs, new File("./data/static_data/spawns"));
		addDirIfValid(dirs, new File("../C\u00f3digo Fonte - Emulador/game-server/data/static_data/spawns"));
		addDirIfValid(dirs, new File("../../C\u00f3digo Fonte - Emulador/game-server/data/static_data/spawns"));
		addDirIfValid(dirs, new File("../Emulador - Produto Final/GameServer/data/static_data/spawns"));
		addDirIfValid(dirs, new File("../../Emulador - Produto Final/GameServer/data/static_data/spawns"));
		addDirIfValid(dirs, new File("../../1 - C\u00f3digo Fonte [Emulador]/game-server/data/static_data/spawns"));
		addDirIfValid(dirs, new File("../../2 - Emulador [Produto Final]/GameServer/data/static_data/spawns"));
		return dirs;
	}

	private static void addDirIfValid(List<File> dirs, File dir) {
		if (dir != null && dir.exists() && dir.isDirectory()) {
			try {
				File canon = dir.getCanonicalFile();
				for (File existing : dirs) {
					if (existing.getCanonicalFile().equals(canon)) {
						return;
					}
				}
				dirs.add(canon);
			} catch (Exception e) {
				dirs.add(dir);
			}
		}
	}

	private static File findXmlFileForSpawn(File spawnsDir, int worldId, int npcId, float origX, float origY, float origZ) {
		List<File> candidates = new ArrayList<>();
		collectXmlFiles(spawnsDir, candidates);

		// Prioriza arquivos que iniciam com o map_id
		String prefix = worldId + "_";
		candidates.sort((f1, f2) -> {
			boolean c1 = f1.getName().startsWith(prefix);
			boolean c2 = f2.getName().startsWith(prefix);
			if (c1 && !c2) return -1;
			if (!c1 && c2) return 1;
			return f1.getName().compareTo(f2.getName());
		});

		for (File f : candidates) {
			if (containsSpawnSpot(f, worldId, npcId, origX, origY, origZ)) {
				return f;
			}
		}
		return null;
	}

	private static void collectXmlFiles(File dir, List<File> list) {
		File[] files = dir.listFiles();
		if (files == null) {
			return;
		}
		for (File f : files) {
			if (f.isDirectory()) {
				// Ignora pastas temporarias New
				if (!f.getName().equalsIgnoreCase("New")) {
					collectXmlFiles(f, list);
				}
			} else if (f.getName().toLowerCase().endsWith(".xml")) {
				list.add(f);
			}
		}
	}

	private static boolean containsSpawnSpot(File file, int worldId, int npcId, float origX, float origY, float origZ) {
		try {
			String content = Files.readString(file.toPath(), StandardCharsets.UTF_8);
			if (!content.contains(String.valueOf(npcId)) || !content.contains(String.valueOf(worldId))) {
				return false;
			}

			Pattern spawnPattern = Pattern.compile("(?i)<spawn\\b[^>]*\\bnpc_id=[\"']" + npcId + "[\"'][^>]*>([\\s\\S]*?)</spawn>");
			Matcher spawnMatcher = spawnPattern.matcher(content);

			while (spawnMatcher.find()) {
				String spawnBody = spawnMatcher.group(1);
				Pattern spotPattern = Pattern.compile("(?i)<spot\\b([^>]*)/?>");
				Matcher spotMatcher = spotPattern.matcher(spawnBody);

				while (spotMatcher.find()) {
					String attrs = spotMatcher.group(1);
					Float sx = parseAttrFloat(attrs, "x");
					Float sy = parseAttrFloat(attrs, "y");
					Float sz = parseAttrFloat(attrs, "z");

					if (sx != null && sy != null && sz != null
							&& Math.abs(sx - origX) < 0.05f
							&& Math.abs(sy - origY) < 0.05f
							&& Math.abs(sz - origZ) < 0.5f) {
						return true;
					}
				}
			}
		} catch (Exception e) {
			log.error("Erro ao ler arquivo XML " + file.getName(), e);
		}
		return false;
	}

	private static boolean modifyXmlFile(File file, int worldId, int npcId, float origX, float origY, float origZ, float newZ, byte newH, boolean onlyHeading) {
		try {
			String content = Files.readString(file.toPath(), StandardCharsets.UTF_8);

			String zFormatted = String.format(Locale.US, "%.4f", newZ);
			if (zFormatted.contains(".")) {
				zFormatted = zFormatted.replaceAll("0+$", "").replaceAll("\\.$", "");
			}

			Pattern spawnPattern = Pattern.compile("(?i)(<spawn\\b[^>]*\\bnpc_id=[\"']" + npcId + "[\"'][^>]*>)([\\s\\S]*?)(</spawn>)");
			Matcher spawnMatcher = spawnPattern.matcher(content);
			StringBuilder sb = new StringBuilder();
			boolean matched = false;

			while (spawnMatcher.find()) {
				String openTag = spawnMatcher.group(1);
				String body = spawnMatcher.group(2);
				String closeTag = spawnMatcher.group(3);

				Pattern spotPattern = Pattern.compile("(?i)(<spot\\b)([^>]*?)(/?>)");
				Matcher spotMatcher = spotPattern.matcher(body);
				StringBuilder bodySb = new StringBuilder();

				while (spotMatcher.find()) {
					String spotOpen = spotMatcher.group(1);
					String attrs = spotMatcher.group(2);
					String spotClose = spotMatcher.group(3);

					Float sx = parseAttrFloat(attrs, "x");
					Float sy = parseAttrFloat(attrs, "y");
					Float sz = parseAttrFloat(attrs, "z");

					if (sx != null && sy != null && sz != null
							&& Math.abs(sx - origX) < 0.05f
							&& Math.abs(sy - origY) < 0.05f
							&& Math.abs(sz - origZ) < 0.5f) {

						String newAttrs = attrs;
						if (!onlyHeading) {
							// Atualiza z
							newAttrs = newAttrs.replaceAll("(?i)\\bz=[\"'][^\"']+[\"']", "z=\"" + zFormatted + "\"");
						}

						// Atualiza ou insere h
						if (Pattern.compile("(?i)\\bh=[\"'][^\"']+[\"']").matcher(newAttrs).find()) {
							newAttrs = newAttrs.replaceAll("(?i)\\bh=[\"'][^\"']+[\"']", "h=\"" + newH + "\"");
						} else {
							// Se nao tinha h, insere antes do fechamento
							if (newAttrs.endsWith(" ")) {
								newAttrs = newAttrs + "h=\"" + newH + "\" ";
							} else {
								newAttrs = newAttrs + " h=\"" + newH + "\"";
							}
						}

						spotMatcher.appendReplacement(bodySb, Matcher.quoteReplacement(spotOpen + newAttrs + spotClose));
						matched = true;
					} else {
						spotMatcher.appendReplacement(bodySb, Matcher.quoteReplacement(spotMatcher.group(0)));
					}
				}
				spotMatcher.appendTail(bodySb);
				spawnMatcher.appendReplacement(sb, Matcher.quoteReplacement(openTag + bodySb.toString() + closeTag));
			}
			spawnMatcher.appendTail(sb);

			if (matched) {
				Files.writeString(file.toPath(), sb.toString(), StandardCharsets.UTF_8);
				log.info("[FixSpawn] Atualizado spawn do NPC {} no arquivo {}", npcId, file.getPath());
				return true;
			}
		} catch (Exception e) {
			log.error("Erro ao modificar XML de spawn " + file.getName(), e);
		}
		return false;
	}

	private static Float parseAttrFloat(String attrs, String attrName) {
		Pattern p = Pattern.compile("(?i)\\b" + attrName + "=[\"']([^\"']+)[\"']");
		Matcher m = p.matcher(attrs);
		if (m.find()) {
			try {
				return Float.parseFloat(m.group(1).trim());
			} catch (NumberFormatException ignored) {
			}
		}
		return null;
	}
}
