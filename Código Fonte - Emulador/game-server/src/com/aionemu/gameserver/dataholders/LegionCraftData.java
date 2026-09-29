package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import javax.xml.bind.Unmarshaller;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlElements;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.items.ItemId;

/**
 * Produção da Legion (legion/legion_craft.xml, gerado do PC/client_guild_craft.xml; só receitas ativas).
 * <p>
 * A lista de uma Legion são as receitas da raça dela, na ordem do id (S 0x15A). Kinah e itens são doados pelos membros (C_GUILD 0x14); o kinah
 * vai no pacote como o item {@link ItemId#KINAH}. Essência e fragmento de essência não são doáveis.
 */
@XmlRootElement(name = "legion_craft")
@XmlAccessorType(XmlAccessType.FIELD)
public class LegionCraftData {

	@XmlElement(name = "recipe", required = true)
	private List<Recipe> recipeList = new ArrayList<>();

	@XmlTransient
	private Map<Integer, Recipe> recipes;

	void afterUnmarshal(Unmarshaller unmarshaller, Object parent) {
		recipes = recipeList.stream().collect(Collectors.toMap(r -> r.id, Function.identity(), (a, b) -> {
			throw new IllegalArgumentException("Duplicate legion craft recipe " + a.id);
		}, java.util.LinkedHashMap::new));
		recipeList = null;
	}

	public Recipe getRecipe(int id) {
		return recipes.get(id);
	}

	public List<Recipe> getRecipes(Race race) {
		return recipes.values().stream().filter(r -> r.race.matches(race)).toList();
	}

	public int size() {
		return recipes.size();
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionCraftRecipe")
	public static class Recipe {

		@XmlAttribute(required = true)
		private int id;

		@XmlAttribute(required = true)
		private String name;

		@XmlAttribute(required = true)
		private LegionDonationData.GroupRace race;

		@XmlAttribute(name = "craft_time", required = true)
		private int craftTime;

		@XmlAttribute(name = "product_id")
		private int productId;

		@XmlAttribute(name = "product_count")
		private int productCount;

		@XmlElements({ @XmlElement(name = "kinah", type = Kinah.class), @XmlElement(name = "item", type = Item.class),
			@XmlElement(name = "essence", type = Essence.class), @XmlElement(name = "essence_piece", type = EssencePiece.class) })
		private List<Component> components = new ArrayList<>();

		public int getId() {
			return id;
		}

		public String getName() {
			return name;
		}

		public int getCraftTime() {
			return craftTime;
		}

		public int getProductId() {
			return productId;
		}

		public int getProductCount() {
			return productCount;
		}

		/**
		 * @return kinah e itens por id crescente, como no S 0x15A oficial (nas receitas 102, 103 e 201 a ordem difere da do XML): os únicos que o
		 *         C_GUILD 0x14 aceita
		 */
		public List<Component> getDonatableComponents() {
			return components.stream().filter(Component::isDonatable).sorted(java.util.Comparator.comparingInt(Component::getItemId)).toList();
		}

		public Component getDonatableComponent(int itemId) {
			return components.stream().filter(c -> c.isDonatable() && c.getItemId() == itemId).findFirst().orElse(null);
		}
	}

	@XmlTransient
	public abstract static class Component {

		public abstract int getItemId();

		public abstract long getCount();

		public abstract int getPoints();

		public boolean isDonatable() {
			return true;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionCraftKinah")
	public static class Kinah extends Component {

		@XmlAttribute(required = true)
		private long amount;

		@Override
		public int getItemId() {
			return ItemId.KINAH;
		}

		@Override
		public long getCount() {
			return amount;
		}

		@Override
		public int getPoints() {
			return 0;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionCraftItem")
	public static class Item extends Component {

		@XmlAttribute(required = true)
		private int id;

		@XmlAttribute(required = true)
		private long count;

		@XmlAttribute(required = true)
		private int points;

		@Override
		public int getItemId() {
			return id;
		}

		@Override
		public long getCount() {
			return count;
		}

		@Override
		public int getPoints() {
			return points;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionCraftEssence")
	public static class Essence extends Component {

		@XmlAttribute(required = true)
		private long count;

		@Override
		public int getItemId() {
			return 0;
		}

		@Override
		public long getCount() {
			return count;
		}

		@Override
		public int getPoints() {
			return 0;
		}

		@Override
		public boolean isDonatable() {
			return false;
		}
	}

	@XmlAccessorType(XmlAccessType.FIELD)
	@XmlType(name = "LegionCraftEssencePiece")
	public static class EssencePiece extends Essence {
	}
}
