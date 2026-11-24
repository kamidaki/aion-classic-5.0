package com.aionemu.gameserver.model.templates.world;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Race;

/**
 * Ponto fixo de ressurreição de um mapa para uma raça (botão de revive no ponto registrado, C_DEAD_RESTART tipo 9).
 * <p>
 * 5.0 oficial (Balic Treasury.pcapng, 29/10): no 800070000 os três revives tipo 9 de um Asmodiano puseram o personagem no mesmo ponto
 * (753, 1460, 1197) do próprio mapa, só com o S_PUT_USER, sem S_WORLD. O cliente nomeia esses pontos no client_world_return
 * (PVPZone_Resurrect_Point_01 = Elyos, _02 = Asmodiano), mas a coordenada só sai da captura.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "WorldResurrectPoint")
public class WorldResurrectPoint {

	@XmlAttribute(name = "race", required = true)
	private Race race;
	@XmlAttribute(name = "x", required = true)
	private float x;
	@XmlAttribute(name = "y", required = true)
	private float y;
	@XmlAttribute(name = "z", required = true)
	private float z;
	@XmlAttribute(name = "h")
	private byte heading;

	public Race getRace() {
		return race;
	}

	public float getX() {
		return x;
	}

	public float getY() {
		return y;
	}

	public float getZ() {
		return z;
	}

	public byte getHeading() {
		return heading;
	}
}
