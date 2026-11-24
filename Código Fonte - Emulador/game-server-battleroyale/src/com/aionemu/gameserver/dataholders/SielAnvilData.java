package com.aionemu.gameserver.dataholders;

import java.util.HashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.*;
import com.aionemu.gameserver.model.templates.item.SielAnvilRecipe;

@XmlRootElement(name = "siel_anvil_recipes")
@XmlAccessorType(XmlAccessType.FIELD)
public class SielAnvilData {
	@XmlElement(name = "recipe")
	private List<SielAnvilRecipe> recipes = new ArrayList<>();
	@XmlTransient
	private final Map<Integer, SielAnvilRecipe> byId = new HashMap<>();

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		for (SielAnvilRecipe recipe : recipes) {
			if (byId.put(recipe.getId(), recipe) != null)
				throw new IllegalArgumentException("Duplicate Siel Anvil recipe " + recipe.getId());
			int total = recipe.getProducts().stream().mapToInt(p -> p.getProbability()).sum();
			if (total > 10000 || total <= 0 || recipe.getMaterials().isEmpty())
				throw new IllegalArgumentException("Invalid Siel Anvil recipe " + recipe.getId());
			if (recipe.getCeilingMax() > 0 && (recipe.getCeilingMinGain() <= 0 || recipe.getCeilingMaxGain() < recipe.getCeilingMinGain()))
				throw new IllegalArgumentException("Invalid Siel Anvil ceiling " + recipe.getId());
			for (var group : recipe.getMaterials())
				group.asMap(); // aggregate repeated ingredients and detect quantity overflow at load time
		}
		recipes = null;
	}

	public SielAnvilRecipe getRecipe(int id) { return byId.get(id); }
	public int size() { return byId.size(); }
}
