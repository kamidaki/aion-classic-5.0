package com.aionemu.gameserver.dataholders;

import com.aionemu.gameserver.model.templates.teleport.TelelocationTemplate;
import gnu.trove.map.hash.TIntObjectHashMap;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.util.List;

/**
 * @author orz
 */
@XmlRootElement(name = "teleport_location")
@XmlAccessorType(XmlAccessType.FIELD)
public class TeleLocationData {

	@XmlElement(name = "teleloc_template")
	private List<TelelocationTemplate> tlist;

	/** A map containing all teleport location templates */
	private TIntObjectHashMap<TelelocationTemplate> loctlistData = new TIntObjectHashMap<TelelocationTemplate>();

	void afterUnmarshal(Unmarshaller u, Object parent) {
		for (TelelocationTemplate loc : tlist) {
			loctlistData.put(loc.getLocId(), loc);
		}
	}

	public int size() {
		return loctlistData.size();
	}

	public TelelocationTemplate getTelelocationTemplate(int id) {
		return loctlistData.get(id);
	}

	/**
	 * Um ponto de chegada conhecido no mapa pedido, ou null se o mapa nao tem nenhum.
	 *
	 * Serve a quem precisa de uma coordenada valida para pousar num mapa e nao pode inventar uma:
	 * estas sao as posicoes para onde o voo oficial leva o jogador.
	 */
	public TelelocationTemplate getPrimeiroDoMapa(int mapId) {
		if (tlist == null) {
			return null;
		}
		for (TelelocationTemplate loc : tlist) {
			if (loc.getMapId() == mapId) {
				return loc;
			}
		}
		return null;
	}

	/** Os mapas que tem ao menos um ponto de chegada, em ordem. */
	public java.util.List<TelelocationTemplate> getPontosDeChegada() {
		java.util.List<TelelocationTemplate> saida = new java.util.ArrayList<TelelocationTemplate>();
		java.util.Set<Integer> vistos = new java.util.HashSet<Integer>();
		if (tlist != null) {
			for (TelelocationTemplate loc : tlist) {
				if (vistos.add(loc.getMapId())) {
					saida.add(loc);
				}
			}
		}
		return saida;
	}
}
