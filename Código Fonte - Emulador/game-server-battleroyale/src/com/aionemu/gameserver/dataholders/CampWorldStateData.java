package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;

/**
 * Estado de mapa que o oficial 5.0 manda ao entrar num mapa de camp war (siege/camp_world_states.xml): variaveis de
 * mundo (S_WORLD_VARIABLE, 0x180) e a lista inteira de zonas (S_ZONE_STATE_LIST, 0x19D). Gerado da captura por
 * {@code 6 - Ferramentas/parsersXML/gera_50_camp_world_states.py}.
 *
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "camp_world_states")
@XmlAccessorType(XmlAccessType.FIELD)
public class CampWorldStateData {

	@XmlElement(name = "camp_world")
	private List<CampWorld> worlds;

	@XmlTransient
	private final Map<Integer, CampWorld> porMapa = new HashMap<>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		porMapa.clear();
		if (worlds != null)
			for (CampWorld w : worlds)
				porMapa.put(w.world, w);
	}

	/** null quando o mapa nao tem camp war. */
	public CampWorld getWorld(int worldId) {
		return porMapa.get(worldId);
	}

	public int size() {
		return porMapa.size();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class CampWorld {

		@XmlAttribute(name = "world", required = true)
		private int world;
		@XmlElement(name = "camp_world_variable")
		private List<Variable> variables;
		@XmlElement(name = "camp_zone_packet")
		private List<ZonePacket> zonePackets;

		public int getWorldId() {
			return world;
		}

		public List<Variable> getVariables() {
			return variables == null ? Collections.emptyList() : variables;
		}

		public List<ZonePacket> getZonePackets() {
			return zonePackets == null ? Collections.emptyList() : zonePackets;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Variable {

		@XmlAttribute(name = "name", required = true)
		private String name;
		@XmlAttribute(name = "value", required = true)
		private int value;

		public String getName() {
			return name;
		}

		public int getValue() {
			return value;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class ZonePacket {

		@XmlElement(name = "camp_zone")
		private List<Zone> zones = new ArrayList<>();

		public List<Zone> getZones() {
			return zones;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	public static class Zone {

		@XmlAttribute(name = "name", required = true)
		private String name;
		@XmlAttribute(name = "camp")
		private int camp;
		@XmlAttribute(name = "state")
		private int state;

		public String getName() {
			return name;
		}

		/** Id da torre cuja vulnerabilidade decide o estado; 0 quando a zona tem estado fixo. */
		public int getCamp() {
			return camp;
		}

		public int getState() {
			return state;
		}
	}
}
