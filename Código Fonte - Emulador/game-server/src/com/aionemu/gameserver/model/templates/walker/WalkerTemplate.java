package com.aionemu.gameserver.model.templates.walker;

import java.util.List;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.spawnengine.WalkerGroupShift;
import com.aionemu.gameserver.spawnengine.WalkerGroupType;

/**
 * @author Lost Academy Team & Durak
 */
@XmlRootElement(name = "walker_template")
@XmlAccessorType(XmlAccessType.FIELD)
public class WalkerTemplate {

	@XmlType(name = "LoopType")
	@XmlEnum
	public enum LoopType {
		NONE,
		NORMAL,
		WALK_BACK
	}

	@XmlElement(name = "routestep", required = true)
	private List<RouteStep> routeStepList;

	@XmlAttribute(name = "route_id", required = true)
	private String routeId;

	@XmlAttribute(name = "pool")
	private int pool = 1;

	@XmlAttribute(name = "formation")
	private WalkerGroupType formation = WalkerGroupType.POINT;

	@XmlAttribute(name = "rows")
	private String rowValues;

	@XmlAttribute(name = "loop_type")
	private LoopType loopType = LoopType.NORMAL;

	@XmlAttribute(name = "offsets")
	private String offsetValues;

	/**
	 * Formação OFFSET: rota própria de cada membro por walker_index, separadas por ";" (vazio = usa o deslocamento de offsets). O
	 * membro anda para o ponto de mesmo índice da sua rota; o grupo continua sincronizado por índice de passo.
	 */
	@XmlAttribute(name = "member_routes")
	private String memberRouteValues;

	@XmlTransient
	private String[] memberRoutes;

	@XmlTransient
	private int[] rows;

	@XmlTransient
	private WalkerGroupShift[] offsets;

	public WalkerTemplate() {
	}

	public WalkerTemplate(String routeId) {
		this.routeId = routeId;
	}

	/**
	 * @param u
	 * @param parent
	 */
	void afterUnmarshal(Unmarshaller u, Object parent) {
		if (loopType == LoopType.WALK_BACK) { // add steps in backward order, so npcs turn and walk the same way back
			for (int i = routeStepList.size() - 2; i > 0; i--) { // skip first and last step
				RouteStep step = routeStepList.get(i);
				routeStepList.add(new RouteStep(step.getX(), step.getY(), step.getZ(), step.getRestTime()));
			}
		}
		for (int i = 0; i < routeStepList.size() - 1; i++) {
			RouteStep step = routeStepList.get(i);
			step.setStepIndex(i);
		}
		RouteStep lastStep = routeStepList.get(routeStepList.size() - 1);
		lastStep.setStepIndex(routeStepList.size() - 1);
		lastStep.setIsLastStep(true);

		if (pool == 2) {
			formation = WalkerGroupType.SQUARE;
			rows = new int[1];
			rows[0] = 2;
		} else if (formation == WalkerGroupType.SQUARE) {
			if (rowValues != null) {
				String[] values = rowValues.split(",");
				rows = new int[values.length];
				for (int i = 0; i < values.length; i++)
					rows[i] = Integer.parseInt(values[i]);
			} else {
				formation = WalkerGroupType.POINT;
			}
		} else if (formation == WalkerGroupType.OFFSET) {
			if (memberRouteValues != null)
				memberRoutes = memberRouteValues.split(";", -1);
			if (offsetValues == null && memberRoutes != null)
				offsetValues = "0:0";
			if (offsetValues != null) {
				String[] membros = offsetValues.split(";");
				offsets = new WalkerGroupShift[membros.length];
				for (int i = 0; i < membros.length; i++) {
					String[] v = membros[i].split(":");
					offsets[i] = new WalkerGroupShift(Float.parseFloat(v[0].trim()), Float.parseFloat(v[1].trim()));
				}
			} else {
				formation = WalkerGroupType.POINT;
			}
		}
		rowValues = null;
		offsetValues = null;
		memberRouteValues = null;
	}

	/**
	 * @return route_id da rota própria do membro com esse walker_index na formação OFFSET, ou null se ele usa o deslocamento
	 */
	public String getMemberRouteId(Integer walkerIndex) {
		int i = walkerIndex == null ? 0 : walkerIndex;
		if (memberRoutes == null || i < 0 || i >= memberRoutes.length)
			return null;
		String r = memberRoutes[i].trim();
		return r.isEmpty() ? null : r;
	}

	/**
	 * @return deslocamento (lado, frente) do membro com esse walker_index na formação OFFSET; (0, 0) se não houver
	 */
	public WalkerGroupShift getOffset(Integer walkerIndex) {
		int i = walkerIndex == null ? 0 : walkerIndex;
		return offsets != null && i >= 0 && i < offsets.length ? offsets[i] : new WalkerGroupShift(0, 0);
	}

	public List<RouteStep> getRouteSteps() {
		return routeStepList;
	}

	public RouteStep getRouteStep(int stepIndex) {
		return routeStepList.get(stepIndex);
	}

	public String getRouteId() {
		return routeId;
	}

	public String getVersionId() {
		return DataManager.WALKER_VERSIONS_DATA.getRouteVersionId(routeId);
	}

	public int getPool() {
		return pool;
	}

	public void setPool(int pool) {
		this.pool = pool;
	}

	public void setRouteSteps(List<RouteStep> newSteps) {
		routeStepList = newSteps;
	}

	public WalkerGroupType getType() {
		return formation;
	}

	public void setType(WalkerGroupType type) {
		formation = type;
	}

	public LoopType getLoopType() {
		return loopType;
	}

	public void setLoopType(LoopType loopType) {
		this.loopType = loopType;
	}

	public int[] getRows() {
		return rows;
	}

	public void setRows(int[] rows) {
		this.rows = rows;
	}

}
