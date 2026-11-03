package com.aionemu.gameserver.model.siege;

import java.util.concurrent.Future;

import com.aionemu.gameserver.model.templates.siegelocation.SiegeLocationTemplate;

/**
 * Torre "Watching Eye" de Tiamaranta Mesa (camp war 5.0).
 * <p>
 * O ciclo foi medido nas capturas oficiais de 2026-09-13 e 2026-09-15:
 * <ul>
 * <li>ao trocar de dono a torre fica <b>protegida</b> por {@link SiegeLocationTemplate#getCampProtectTime()} segundos
 * (300 Tower_S, 600 Tower_M, 900 Tower_L). Nessa fase nao existe boss nem MistOn e a zona PvP fica desligada;</li>
 * <li>depois fica <b>vulneravel</b>: nascem o boss e o MistOn e a zona PvP liga;</li>
 * <li>se for de uma raca e ninguem tomar em {@link SiegeLocationTemplate#getCampResetTime()} segundos, os Balaur
 * retomam. Torre de Balaur fica vulneravel sem prazo, ate alguem matar o boss.</li>
 * </ul>
 * Torre com {@code camp_reset_time} 0 (no cliente, {@code camp_war_reset_time} 40000000) nao entra no ciclo: fica
 * protegida para sempre, como nas capturas.
 *
 * @author Lost Academy Team & Durak
 */
public class CampLocation extends SiegeLocation {

	private volatile long phaseEndMillis;
	private volatile Future<?> phaseTask;

	public CampLocation(SiegeLocationTemplate template) {
		super(template);
		setRace(template.getCampDefaultRace());
	}

	public int getProtectTime() {
		return getTemplate().getCampProtectTime();
	}

	public int getResetTime() {
		return getTemplate().getCampResetTime();
	}

	public String getPvpZoneName() {
		return getTemplate().getCampPvpZone();
	}

	/** Torre desligada pela Gameforge: nao troca de estado nem de dono. */
	public boolean isStatic() {
		return getResetTime() == 0;
	}

	/** Instante em que a fase corrente acaba; 0 quando a fase nao tem prazo (vulneravel dos Balaur). */
	public long getPhaseEndMillis() {
		return phaseEndMillis;
	}

	public void setPhaseEndMillis(long phaseEndMillis) {
		this.phaseEndMillis = phaseEndMillis;
	}

	/** Segundos que faltam para a fase acabar, arredondados para cima; 0 quando nao ha prazo. */
	public int getRemainingPhaseSeconds() {
		long fim = phaseEndMillis;
		if (fim == 0)
			return 0;
		long falta = fim - System.currentTimeMillis();
		return falta <= 0 ? 0 : (int) ((falta + 999) / 1000);
	}

	public Future<?> getPhaseTask() {
		return phaseTask;
	}

	public void setPhaseTask(Future<?> phaseTask) {
		this.phaseTask = phaseTask;
	}
}
