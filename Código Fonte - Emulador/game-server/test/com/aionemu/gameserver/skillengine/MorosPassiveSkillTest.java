package com.aionemu.gameserver.skillengine;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import javax.xml.bind.JAXBContext;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.stream.StreamSource;

import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;

/**
 * Passivas do Moreth (Moros_Promise) contra o client_skills.xml: sem a chance do provoker elas disparavam o proc em todo ataque, e sem a
 * restrição de raça o proc valia contra qualquer alvo (visto em jogo em 28/09).
 */
class MorosPassiveSkillTest {

	private static final Path SKILLS = Path.of("data", "static_data", "skills", "skill_templates.xml");
	private static final Path PRODUCT_SKILLS = Path.of("..", "..", "Emulador - Produto Final", "GameServer", "data", "static_data", "skills",
		"skill_templates.xml");
	private static final Path CLIENT_SKILLS = resolveClientData().resolve(Path.of("data", "skills", "client_skills.xml"));
	/** passiva -> proc que ela dispara (effect1_reserved17 do cliente) */
	private static final Map<Integer, Integer> PASSIVAS = Map.of(2544, 8775, 2550, 9134, 3942, 9134, 4270, 9267);
	private static final List<Integer> PROCS = List.of(8775, 9134, 9267);

	@Test
	void provokerChanceComesFromTheClient() throws Exception {
		assumeTrue(Files.exists(CLIENT_SKILLS), "Dados extraídos do cliente 5.0 não estão disponíveis neste checkout");
		Map<Integer, Element> cliente = clientById(parse(CLIENT_SKILLS));
		Map<Integer, Element> servidor = templateById(parse(SKILLS));
		for (Map.Entry<Integer, Integer> passiva : PASSIVAS.entrySet()) {
			Element template = servidor.get(passiva.getKey());
			assertNotNull(template, "template " + passiva.getKey());
			Element provoker = (Element) template.getElementsByTagName("provoker").item(0);
			assertNotNull(provoker, "provoker de " + passiva.getKey());
			assertEquals(String.valueOf(passiva.getValue()), provoker.getAttribute("skill_id"), "proc de " + passiva.getKey());

			Element oficial = cliente.get(passiva.getKey());
			String prob1 = text(oficial, "effect1_reserved_cond1_prob1");
			String prob2 = text(oficial, "effect1_reserved_cond1_prob2");
			String esperado = !"0".equals(prob1) ? prob1 : prob2;
			assertEquals(esperado, provoker.getAttribute("hittypeprob2"), "chance do provoker de " + passiva.getKey());
			assertNotEquals("", provoker.getAttribute("hittypeprob2"), "sem hittypeprob2 o EffectTemplate usa 100 e o proc sai em todo ataque");
		}
	}

	@Test
	void procsOnlyHitTheRacesTheClientAllows() throws Exception {
		Map<Integer, Element> servidor = templateById(parse(SKILLS));
		for (int proc : PROCS)
			assertEquals("DRAKAN LIZARDMAN NAGA", servidor.get(proc).getAttribute("target_races"), "raças do proc " + proc);
	}

	@Test
	void productDataMatchesTheSource() throws Exception {
		assumeTrue(Files.exists(PRODUCT_SKILLS), "Produto Final não está neste checkout");
		Map<Integer, Element> fonte = templateById(parse(SKILLS));
		Map<Integer, Element> produto = templateById(parse(PRODUCT_SKILLS));
		for (int skillId : List.of(2544, 2550, 3942, 4270, 8775, 9134, 9267))
			assertEquals(serialize(fonte.get(skillId)), serialize(produto.get(skillId)), "template " + skillId + " fora de sincronia");
	}

	@Test
	void targetRacesFilterOnlyTheListedRaces() throws Exception {
		String xml = """
			<skill_template skill_id="8775" name="proc" nameId="1" stack="TESTE" skilltype="MAGICAL" skillsubtype="ATTACK" \
			activation="PROVOKED" target_races="DRAKAN LIZARDMAN NAGA" duration="0"/>""";
		SkillTemplate template = JAXBContext.newInstance(SkillTemplate.class).createUnmarshaller()
			.unmarshal(new StreamSource(new StringReader(xml)), SkillTemplate.class).getValue();
		assertEquals(List.of(Race.DRAKAN, Race.LIZARDMAN, Race.NAGA), template.getTargetRaces());
		assertFalse(template.canTargetRace(null), "sem alvo não há raça para conferir");

		String semRestricao = """
			<skill_template skill_id="1" name="qualquer" nameId="1" stack="TESTE" skilltype="MAGICAL" skillsubtype="ATTACK" \
			activation="ACTIVE" duration="0"/>""";
		SkillTemplate livre = JAXBContext.newInstance(SkillTemplate.class).createUnmarshaller()
			.unmarshal(new StreamSource(new StringReader(semRestricao)), SkillTemplate.class).getValue();
		assertTrue(livre.getTargetRaces().isEmpty());
		assertTrue(livre.canTargetRace(null), "skill sem restrição continua valendo contra qualquer alvo");
	}

	private static Path resolveClientData() {
		Path legacy = Path.of("..", "..", "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos");
		Path canonical = Path.of("..", "..", "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos");
		return Files.exists(canonical) ? canonical : legacy;
	}

	private static Document parse(Path path) throws Exception {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
		factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
		factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
		return factory.newDocumentBuilder().parse(path.toFile());
	}

	private static Map<Integer, Element> templateById(Document document) {
		return byId(document.getElementsByTagName("skill_template"), element -> Integer.parseInt(element.getAttribute("skill_id")));
	}

	private static Map<Integer, Element> clientById(Document document) {
		return byId(document.getElementsByTagName("skill_base_client"), element -> Integer.parseInt(text(element, "id")));
	}

	private static Map<Integer, Element> byId(NodeList nodes, java.util.function.ToIntFunction<Element> id) {
		Map<Integer, Element> result = new java.util.HashMap<>();
		for (int i = 0; i < nodes.getLength(); i++) {
			Element element = (Element) nodes.item(i);
			result.put(id.applyAsInt(element), element);
		}
		return result;
	}

	private static String text(Element element, String tagName) {
		NodeList nodes = element.getElementsByTagName(tagName);
		return nodes.getLength() == 0 ? "0" : nodes.item(0).getTextContent().trim();
	}

	private static String serialize(Element element) throws Exception {
		assertNotNull(element);
		java.io.StringWriter writer = new java.io.StringWriter();
		javax.xml.transform.TransformerFactory.newInstance().newTransformer()
			.transform(new javax.xml.transform.dom.DOMSource(element), new javax.xml.transform.stream.StreamResult(writer));
		return writer.toString();
	}
}
