package com.aionemu.gameserver.skillengine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.xml.parsers.DocumentBuilderFactory;

import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

import com.aionemu.gameserver.skillengine.effect.BufEffect;
import com.aionemu.gameserver.skillengine.effect.UtilityEffect;

/**
 * Invariantes da auditoria de Skills Classic 5.0.
 * <p>
 * Estes testes nao afirmam equivalencia funcional com o oficial. Eles impedem
 * regressao estrutural e tornam as lacunas conhecidas explicitas ate que sejam
 * corrigidas com evidencia.
 */
class SkillStaticDataAuditTest {

	private static final Path SKILLS = Path.of("data", "static_data", "skills", "skill_templates.xml");
	private static final Path SKILLS_XSD = Path.of("data", "static_data", "skills", "skills.xsd");
	private static final Path SKILL_TREE = Path.of("data", "static_data", "skill_tree", "skill_tree.xml");
	private static final Path NPC_SKILLS = Path.of("data", "static_data", "npc_skills", "npc_skills.xml");
	private static final Path PRODUCT_SKILLS = Path.of("..", "..", "Emulador - Produto Final", "GameServer-GameForge", "data", "static_data", "skills",
		"skill_templates.xml");
	private static final Path CLIENT_DATA = resolveClientData();
	private static final Path CLIENT_SKILLS = CLIENT_DATA.resolve(Path.of("data", "skills", "client_skills.xml"));
	private static final Path CLIENT_MESSAGES = CLIENT_DATA.resolve(Path.of("data", "Strings", "client_strings_msg.xml"));
	private static final Path SYSTEM_MESSAGES = Path.of("src", "com", "aionemu", "gameserver", "network", "aion", "serverpackets",
		"SM_SYSTEM_MESSAGE.java");
	private static final Path SKILL_ENGINE_SOURCE = Path.of("src", "com", "aionemu", "gameserver", "skillengine");

	private static final Set<Integer> KNOWN_OFFICIAL_MISSING = Set.of(50068);
	private static final Set<Integer> KNOWN_SERVER_ONLY = Set.of(418, 459, 460, 854, 993, 1120, 1129, 1264, 1266, 1514, 2075, 2381, 2382,
		2383, 2384, 2385, 2386, 2387, 2388, 8397, 21922, 21923, 21924, 21925, 21926, 21927);
	private static final Set<String> SUPPORTED_TARGET_TYPES = Set.of("ONLYONE", "PARTY", "AREA", "PARTY_WITHPET", "POINT");

	@Test
	void skillIdsAreUniqueAndKnownCoverageGapsCannotChangeSilently() throws Exception {
		requireClientData();
		Set<Integer> serverIds = templateIds(parse(SKILLS));
		Set<Integer> officialIds = clientIds(parse(CLIENT_SKILLS));

		Set<Integer> officialMissing = new HashSet<>(officialIds);
		officialMissing.removeAll(serverIds);
		Set<Integer> serverOnly = new HashSet<>(serverIds);
		serverOnly.removeAll(officialIds);

		assertEquals(12_114, officialIds.size(), "A fonte oficial mudou; regenere a matriz antes de aceitar o novo total");
		assertEquals(12_139, serverIds.size(), "O total de templates mudou; regenere a matriz e classifique cada ID");
		assertEquals(KNOWN_OFFICIAL_MISSING, officialMissing, "Skills oficiais ausentes mudaram sem atualizar a auditoria");
		assertEquals(KNOWN_SERVER_ONLY, serverOnly, "Templates sem fonte oficial mudaram sem atualizar a auditoria");
	}

	@Test
	void playerAndNpcSkillReferencesResolveToTemplates() throws Exception {
		Set<Integer> templates = templateIds(parse(SKILLS));
		Set<Integer> missingPlayer = referencedIds(parse(SKILL_TREE), "skill", "skillId", templates);
		Set<Integer> missingNpc = referencedIds(parse(NPC_SKILLS), "npc_skill", "id", templates);

		assertTrue(missingPlayer.isEmpty(), "Skill tree referencia templates ausentes: " + missingPlayer);
		assertTrue(missingNpc.isEmpty(), "NPC skills referenciam templates ausentes: " + missingNpc);
	}

	@Test
	void everyEffectTagIsDeclaredInSkillsXsd() throws Exception {
		String xsd = Files.readString(SKILLS_XSD, StandardCharsets.UTF_8);
		int effectsStart = xsd.indexOf("<xs:complexType name=\"Effects\">");
		int effectsEnd = xsd.indexOf("</xs:complexType>", effectsStart);
		assertTrue(effectsStart >= 0 && effectsEnd > effectsStart, "ComplexType Effects nao encontrado no XSD");

		Set<String> declared = new HashSet<>();
		Matcher matcher = Pattern.compile("<xs:element\\s+name=\"([^\"]+)\"").matcher(xsd.substring(effectsStart, effectsEnd));
		while (matcher.find())
			declared.add(matcher.group(1));

		Set<String> unknown = new HashSet<>();
		NodeList effectGroups = parse(SKILLS).getElementsByTagName("effects");
		for (int i = 0; i < effectGroups.getLength(); i++) {
			NodeList effects = effectGroups.item(i).getChildNodes();
			for (int j = 0; j < effects.getLength(); j++) {
				Node effect = effects.item(j);
				if (effect.getNodeType() == Node.ELEMENT_NODE && !declared.contains(effect.getNodeName()))
					unknown.add(effect.getNodeName());
			}
		}
		assertTrue(unknown.isEmpty(), "Efeitos usados no XML sem declaracao no XSD: " + unknown);
	}

	@Test
	void sourceAndProductSkillTemplatesAreByteIdentical() throws Exception {
		assertTrue(Files.exists(PRODUCT_SKILLS), "Template do produto final nao encontrado: " + PRODUCT_SKILLS);
		assertEquals(-1, Files.mismatch(SKILLS, PRODUCT_SKILLS), "Fonte e produto final possuem skill_templates.xml diferentes");
	}

	@Test
	void utilityEffectsApplyTheirDeclaredStatChangesAsBuffs() {
		assertTrue(BufEffect.class.isAssignableFrom(UtilityEffect.class),
			"UtilityEffect deve registrar e remover os atributos declarados pelas Skills 2521-2523");
	}

	@Test
	void skillEngineUsesOnlySystemMessagesPresentInClassicClient() throws Exception {
		requireClientData();
		Set<Integer> officialMessageIds = childElementIds(parse(CLIENT_MESSAGES), "string", "id");
		String factoriesSource = Files.readString(SYSTEM_MESSAGES, StandardCharsets.UTF_8);
		Matcher factoryMatcher = Pattern.compile(
			"public static SM_SYSTEM_MESSAGE\\s+(\\w+)\\([^)]*\\)\\s*\\{.*?new SM_SYSTEM_MESSAGE\\((\\d+)", Pattern.DOTALL)
			.matcher(factoriesSource);
		Map<String, Integer> factoryIds = new HashMap<>();
		while (factoryMatcher.find())
			factoryIds.put(factoryMatcher.group(1), Integer.parseInt(factoryMatcher.group(2)));

		Set<String> missingFactories = new HashSet<>();
		Map<String, Integer> invalidIds = new HashMap<>();
		Pattern usagePattern = Pattern.compile("SM_SYSTEM_MESSAGE\\.(\\w+)\\(");
		try (var paths = Files.walk(SKILL_ENGINE_SOURCE)) {
			for (Path path : paths.filter(p -> p.toString().endsWith(".java")).toList()) {
				Matcher usageMatcher = usagePattern.matcher(Files.readString(path, StandardCharsets.UTF_8));
				while (usageMatcher.find()) {
					String factory = usageMatcher.group(1);
					Integer id = factoryIds.get(factory);
					if (id == null)
						missingFactories.add(factory);
					else if (!officialMessageIds.contains(id))
						invalidIds.put(factory, id);
				}
			}
		}

		assertTrue(missingFactories.isEmpty(), "Factories de mensagem ausentes: " + missingFactories);
		assertTrue(invalidIds.isEmpty(), "Mensagens usadas por Skills ausentes no cliente Classic 5.0: " + invalidIds);
	}

	@Test
	void skillTargetRangesMatchClassicClient() throws Exception {
		requireClientData();
		Map<Integer, Element> official = clientElementsById(parse(CLIENT_SKILLS));
		NodeList templates = parse(SKILLS).getElementsByTagName("skill_template");
		Set<String> differences = new HashSet<>();
		for (int i = 0; i < templates.getLength(); i++) {
			Element template = (Element) templates.item(i);
			int skillId = Integer.parseInt(template.getAttribute("skill_id"));
			Element client = official.get(skillId);
			if (client == null)
				continue;
			NodeList propertyNodes = template.getElementsByTagName("properties");
			if (propertyNodes.getLength() == 0)
				continue;
			Element properties = (Element) propertyNodes.item(0);
			compareIntAttribute(differences, skillId, properties, "first_target_range", clientText(client, "first_target_valid_distance"));
			compareIntAttribute(differences, skillId, properties, "revision_distance", clientText(client, "revision_distance"));
			compareIntAttribute(differences, skillId, properties, "target_distance", clientText(client, "target_range_opt1"));
			boolean expectedWeaponRange = "1".equals(clientText(client, "add_wpn_range"));
			boolean actualWeaponRange = "true".equals(properties.getAttribute("awr"));
			if (expectedWeaponRange != actualWeaponRange)
				differences.add(skillId + ":awr=" + actualWeaponRange + "!=" + expectedWeaponRange);

			String expectedFirstTarget = clientText(client, "first_target").toUpperCase();
			if (!expectedFirstTarget.isEmpty() && !expectedFirstTarget.equals(properties.getAttribute("first_target")))
				differences.add(skillId + ":first_target=" + properties.getAttribute("first_target") + "!=" + expectedFirstTarget);
			String expectedTargetType = clientText(client, "target_range").toUpperCase();
			if (SUPPORTED_TARGET_TYPES.contains(expectedTargetType) && !expectedTargetType.equals(properties.getAttribute("target_type")))
				differences.add(skillId + ":target_type=" + properties.getAttribute("target_type") + "!=" + expectedTargetType);
		}
		assertTrue(differences.isEmpty(), "Alcances divergentes do cliente Classic 5.0: " + differences);
	}

	private static Document parse(Path path) throws Exception {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
		factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
		factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
		return factory.newDocumentBuilder().parse(path.toFile());
	}

	private static Path resolveClientData() {
		Path legacy = Path.of("..", "..", "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos");
		Path canonical = Path.of("..", "..", "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos");
		return Files.exists(canonical) ? canonical : legacy;
	}

	private static void requireClientData() {
		assumeTrue(Files.exists(CLIENT_SKILLS) && Files.exists(CLIENT_MESSAGES),
			"Dados extraídos do cliente 5.0 não estão disponíveis neste checkout");
	}

	private static Set<Integer> templateIds(Document document) {
		return uniqueIds(document.getElementsByTagName("skill_template"), "skill_id");
	}

	private static Set<Integer> clientIds(Document document) {
		NodeList skills = document.getElementsByTagName("skill_base_client");
		Map<Integer, Integer> counts = new HashMap<>();
		for (int i = 0; i < skills.getLength(); i++) {
			Element skill = (Element) skills.item(i);
			int id = Integer.parseInt(skill.getElementsByTagName("id").item(0).getTextContent());
			counts.merge(id, 1, Integer::sum);
		}
		assertTrue(counts.values().stream().allMatch(count -> count == 1), "IDs duplicados na fonte oficial: " + duplicates(counts));
		return counts.keySet();
	}

	private static Set<Integer> childElementIds(Document document, String tagName, String idTagName) {
		Set<Integer> ids = new HashSet<>();
		NodeList nodes = document.getElementsByTagName(tagName);
		for (int i = 0; i < nodes.getLength(); i++) {
			Element element = (Element) nodes.item(i);
			ids.add(Integer.parseInt(element.getElementsByTagName(idTagName).item(0).getTextContent()));
		}
		return ids;
	}

	private static Map<Integer, Element> clientElementsById(Document document) {
		Map<Integer, Element> result = new HashMap<>();
		NodeList skills = document.getElementsByTagName("skill_base_client");
		for (int i = 0; i < skills.getLength(); i++) {
			Element skill = (Element) skills.item(i);
			result.put(Integer.parseInt(clientText(skill, "id")), skill);
		}
		return result;
	}

	private static String clientText(Element client, String tagName) {
		NodeList nodes = client.getElementsByTagName(tagName);
		return nodes.getLength() == 0 ? "" : nodes.item(0).getTextContent().trim();
	}

	private static void compareIntAttribute(Set<String> differences, int skillId, Element properties, String attribute, String expectedText) {
		int expected = expectedText.isEmpty() ? 0 : (int) Double.parseDouble(expectedText);
		String actualText = properties.getAttribute(attribute);
		int actual = actualText.isEmpty() ? 0 : Integer.parseInt(actualText);
		if (actual != expected)
			differences.add(skillId + ":" + attribute + "=" + actual + "!=" + expected);
	}

	private static Set<Integer> uniqueIds(NodeList nodes, String attribute) {
		Map<Integer, Integer> counts = new HashMap<>();
		for (int i = 0; i < nodes.getLength(); i++) {
			Element element = (Element) nodes.item(i);
			counts.merge(Integer.parseInt(element.getAttribute(attribute)), 1, Integer::sum);
		}
		assertTrue(counts.values().stream().allMatch(count -> count == 1), "IDs duplicados em " + attribute + ": " + duplicates(counts));
		return counts.keySet();
	}

	private static Set<Integer> duplicates(Map<Integer, Integer> counts) {
		Set<Integer> duplicates = new HashSet<>();
		counts.forEach((id, count) -> {
			if (count > 1)
				duplicates.add(id);
		});
		return duplicates;
	}

	private static Set<Integer> referencedIds(Document document, String tagName, String attribute, Set<Integer> templates) {
		Set<Integer> missing = new HashSet<>();
		NodeList nodes = document.getElementsByTagName(tagName);
		for (int i = 0; i < nodes.getLength(); i++) {
			String value = ((Element) nodes.item(i)).getAttribute(attribute);
			if (!value.isEmpty()) {
				int id = Integer.parseInt(value);
				if (!templates.contains(id))
					missing.add(id);
			}
		}
		return missing;
	}
}
