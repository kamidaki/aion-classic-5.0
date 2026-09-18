import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.List;
import com.aionemu.gameserver.model.templates.item.SielAnvilRecipe;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;
import com.aionemu.gameserver.network.aion.clientpackets.CM_SIEL_ANVIL_CANCEL;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UNK_01AB;
import javax.xml.XMLConstants;
import javax.xml.bind.JAXBContext;
import javax.xml.validation.SchemaFactory;
import com.aionemu.gameserver.dataholders.SielAnvilData;
import com.aionemu.gameserver.dataholders.StaticData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.items.storage.PlayerStorage;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.services.craft.SielAnvilService;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.clientpackets.CM_SIEL_ANVIL;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_ANVIL_START;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_ANVIL_RESULT;

/** Standalone regression checks against official capture payloads; no database or live server needed. */
class SielAnvilChecks {
	private static int checks;
	private static void check(boolean value, String message) {
		checks++;
		if (!value) throw new AssertionError(message);
	}
	private static Object field(Object target, String name) throws Exception {
		var field = target.getClass().getDeclaredField(name);
		field.setAccessible(true);
		return field.get(target);
	}
	private static CM_SIEL_ANVIL parse(byte[] bytes) throws Exception {
		var packet = new CM_SIEL_ANVIL(0x1FA, EnumSet.of(State.IN_GAME));
		packet.setBuffer(ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN));
		var read = CM_SIEL_ANVIL.class.getDeclaredMethod("readImpl");
		read.setAccessible(true);
		read.invoke(packet);
		return packet;
	}
	private static String payload(AionServerPacket packet) throws Exception {
		var buffer = ByteBuffer.allocate(64).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		var write = packet.getClass().getDeclaredMethod("writeImpl", AionConnection.class);
		write.setAccessible(true);
		write.invoke(packet, new Object[] { null });
		return HexFormat.of().formatHex(Arrays.copyOf(buffer.array(), buffer.position()));
	}
	public static void main(String[] args) throws Exception {
		Path data = Path.of(args[0]);
		for (String requiredClass : List.of("com.aionemu.gameserver.spawnengine.TemporarySpawnEngine",
			"com.aionemu.gameserver.restrictions.PlayerRestrictions", "com.aionemu.gameserver.services.player.PlayerLeaveWorldService"))
			check(Class.forName(requiredClass, false, SielAnvilChecks.class.getClassLoader()) != null, "Production class load: " + requiredClass);
		var schemas = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
		var unmarshaller = JAXBContext.newInstance(SielAnvilData.class).createUnmarshaller();
		unmarshaller.setSchema(schemas.newSchema(data.resolve("items/siel_anvil.xsd").toFile()));
		var recipes = (SielAnvilData) unmarshaller.unmarshal(data.resolve("items/siel_anvil.xml").toFile());
		check(recipes.size() == 388, "All client recipes imported");
		schemas.newSchema(data.resolve("static_data.xsd").toFile());
		JAXBContext.newInstance(StaticData.class);
		check(true, "Integrated schema and JAXB boot model");
		var recipe = recipes.getRecipe(170);
		check(recipe.isEnabled(), "Captured recipe enabled");
		Map<Integer, Long> costs = Map.of(166300000, 4L, 182400001, 400000L);
		check(recipe.match(costs) != null, "Official ingredients and Kinah cost");
		var inventory = new PlayerStorage(null, StorageType.CUBE);
		var gold = new ItemTemplate();
		var itemId = ItemTemplate.class.getDeclaredField("itemId");
		itemId.setAccessible(true);
		itemId.setInt(gold, 182400001);
		inventory.add_CharacterTransfer(new Item(1, gold, 400000, false, 0));
		var essence = new ItemTemplate();
		itemId.setInt(essence, 166300000);
		inventory.add_CharacterTransfer(new Item(2, essence, 4, false, 0));
		var hasMaterials = SielAnvilService.class.getDeclaredMethod("hasMaterials", Storage.class, Map.class);
		hasMaterials.setAccessible(true);
		check(inventory.getItemCountByItemId(182400001) == 0, "Kinah resides outside ordinary inventory");
		check((boolean) hasMaterials.invoke(null, inventory, costs), "Service validates actual Kinah wallet and ingredients");
		check(!(boolean) hasMaterials.invoke(null, inventory, Map.of(166300000, 5L, 182400001, 400000L)), "Insufficient essence rejected");
		check(!(boolean) hasMaterials.invoke(null, inventory, Map.of(166300000, 4L, 182400001, 400001L)), "Insufficient Kinah rejected");
		check(recipe.match(Map.of(166300000, 4L)) == null, "Missing Kinah rejected");
		check(recipe.match(Map.of(166300000, 2L, 182400001, 200000L)) == null, "Other client variant rejected");
		check(recipe.match(Map.of(166300000, 4L, 182400001, 400001L)) == null, "Tampered cost rejected");
		var slots = SielAnvilService.class.getDeclaredMethod("maximumSlots", int.class, long[][].class, long[].class, long[].class, int[].class, int.class);
		slots.setAccessible(true);
		check((long) slots.invoke(null, 50, new long[][] {{1, 0}, {0, 1}}, new long[] {1, 1}, new long[] {0, 0}, new int[] {0, 0}, 0) == 50,
			"50 attempts need 50 slots for mutually exclusive non-stackable products");
		check((long) slots.invoke(null, 50, new long[][] {{1, 0}, {0, 1}}, new long[] {1000, 1000}, new long[] {0, 0}, new int[] {0, 0}, 0) == 2,
			"Mixed stackable batch reserves both product stacks");
		check((long) slots.invoke(null, 1, new long[][] {{1, 0}, {0, 1}, {0, 0}}, new long[] {1, 1}, new long[] {0, 0}, new int[] {0, 0}, 0) == 1,
			"Single craft does not reserve mutually exclusive rewards together");
		check((long) slots.invoke(null, 10, new long[][] {{1}, {2}, {3}}, new long[] {10}, new long[] {10}, new int[] {0}, 0) == 2,
			"Shared reward ids and existing stack capacity handled once");
		int first = 0, second = 0;
		for (int roll = 0; roll < 10000; roll++) {
			var product = recipe.selectProduct(roll);
			if (product.getIndex() == 1) first++;
			if (product.getIndex() == 2) second++;
		}
		check(first == 8000 && second == 2000, "Exact 80/20 probability boundaries");
		check(recipe.selectProduct(9999).getItemId() == 174000001, "Captured product ordinal 2 maps to delivered item");
		check(recipes.getRecipe(1).selectProduct(9999) == null, "Failure probability retained");
		check(recipes.getRecipe(102).isEnabled(), "Ring ceiling recipe enabled");
		var ring = recipes.getRecipe(102);
		check(ring.nextCeiling(980, false, 30) == 1000, "Failure ceiling progress capped at official maximum");
		check(ring.nextCeiling(1000, true, 30) == 0, "Success resets ceiling progress");
		var resolve = SielAnvilService.class.getDeclaredMethod("resolveCosts", Storage.class, SielAnvilRecipe.class,
			int.class, int.class, Map.class, List.class);
		resolve.setAccessible(true);
		check(resolve.invoke(null, inventory, recipe, 0, 2, costs, List.of()).equals(Map.of(166300000, 8L, 182400001, 800000L)), "Batch pays every attempt at server costs");
		check(resolve.invoke(null, inventory, recipe, 1, 1, costs, List.of()) == null, "Nonexistent alternative rejected");
		var alternative = recipes.getRecipe(2).getMaterials().get(1).asMap();
		check(resolve.invoke(null, inventory, recipes.getRecipe(2), 1, 1, alternative, List.of()).equals(alternative), "Official alternative group accepted");
		check(resolve.invoke(null, inventory, recipes.getRecipe(2), 0, 1, alternative, List.of()) == null, "Group and ingredients must agree");
		var wing = new ItemTemplate();
		itemId.setInt(wing, 187000069);
		inventory.add_CharacterTransfer(new Item(3, wing, 1, false, 0));
		inventory.add_CharacterTransfer(new Item(4, wing, 1, false, 0));
		var wingRecipe = recipes.getRecipe(84);
		Map<Integer, Long> ordinary = new java.util.HashMap<>(wingRecipe.getMaterials().getFirst().asMap());
		ordinary.remove(187000069);
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of(3)).equals(wingRecipe.getMaterials().getFirst().asMap()), "Selected wing object resolves to canonical cost");
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of()) == null, "No automatic equipment substitution");
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of(3, 3)) == null, "Selected object cannot be reused");
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of(3, 4)) == null, "Excess selected equipment rejected");
		check(resolve.invoke(null, inventory, wingRecipe, 0, 2, ordinary, List.of(3)) == null, "Equipment selection limited to one attempt as client UI");
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of(999)) == null, "Foreign or missing object rejected");
		inventory.getItemByObjId(3).setEquipped(true);
		check(resolve.invoke(null, inventory, wingRecipe, 0, 1, ordinary, List.of(3)) == null, "Equipped wing rejected");
		inventory.getItemByObjId(3).setEquipped(false);
		byte[] wingRequest = ByteBuffer.allocate(25).order(ByteOrder.LITTLE_ENDIAN)
			.putInt(84).putInt(0).putShort((short) 1).putInt(3).putShort((short) 1)
			.putInt(188100282).putInt(50).put((byte) 1).array();
		var selectedPacket = parse(wingRequest);
		check((boolean) field(selectedPacket, "valid"), "Canonical selected wing request fully parsed");
		check(resolve.invoke(null, inventory, wingRecipe, (int) field(selectedPacket, "groupIndex"),
			(int) field(selectedPacket, "quantity"), field(selectedPacket, "materials"), field(selectedPacket, "selectedObjects"))
			.equals(wingRecipe.getMaterials().getFirst().asMap()), "Selected packet and canonical recipe agree through service resolution");
		var ringMaterial = new ItemTemplate();
		itemId.setInt(ringMaterial, 122001590);
		inventory.add_CharacterTransfer(new Item(5, ringMaterial, 1, false, 0));
		inventory.add_CharacterTransfer(new Item(6, ringMaterial, 1, false, 0));
		byte[] firstRingRequest = null;
		for (int groupIndex = 0; groupIndex < ring.getMaterials().size(); groupIndex++) {
			Map<Integer, Long> ringOrdinary = new java.util.TreeMap<>(ring.getMaterials().get(groupIndex).asMap());
			int selectedCount = ringOrdinary.remove(122001590).intValue();
			var ringWire = ByteBuffer.allocate(13 + selectedCount * 4 + ringOrdinary.size() * 8).order(ByteOrder.LITTLE_ENDIAN);
			ringWire.putInt(102).putInt(groupIndex).putShort((short) selectedCount);
			for (int i = 0; i < selectedCount; i++) ringWire.putInt(5 + i);
			ringWire.putShort((short) ringOrdinary.size());
			ringOrdinary.forEach((id, count) -> ringWire.putInt(id).putInt(count.intValue()));
			ringWire.put((byte) 1);
			if (groupIndex == 0) firstRingRequest = ringWire.array().clone();
			var ringPacket = parse(ringWire.array());
			check((boolean) field(ringPacket, "valid"), "Ring selected request parsed for group " + groupIndex);
			check(resolve.invoke(null, inventory, ring, groupIndex, 1, field(ringPacket, "materials"), field(ringPacket, "selectedObjects"))
				.equals(ring.getMaterials().get(groupIndex).asMap()), "Ring selected objects resolve repeated ingredients for group " + groupIndex);
		}
		ByteBuffer.wrap(firstRingRequest).order(ByteOrder.LITTLE_ENDIAN).putInt(14, 5);
		var reusedRing = parse(firstRingRequest);
		check(!(boolean) field(reusedRing, "valid"), "Packet cannot reuse one ring for two selected slots");
		check(field(reusedRing, "selectedObjects").equals(List.of(5, 5)), "Rejected request retains selected ids for diagnosis");
		check(((Map<?, ?>) field(reusedRing, "materials")).size() == 3, "Rejected request retains ordinary materials for diagnosis");
		// Allocate only the player shell; do not initialize world, threads, connections or a database.
		var unsafeField = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
		unsafeField.setAccessible(true);
		var unsafe = (sun.misc.Unsafe) unsafeField.get(null);
		var player = (Player) unsafe.allocateInstance(Player.class);
		var inventoryField = Player.class.getDeclaredField("inventory");
		inventoryField.setAccessible(true);
		inventoryField.set(player, inventory);
		var taskClass = Class.forName("com.aionemu.gameserver.services.craft.SielAnvilService$CraftTask");
		var taskConstructor = taskClass.getDeclaredConstructor(Player.class, SielAnvilRecipe.class, Map.class, List.class, int.class);
		taskConstructor.setAccessible(true);
		var task = (AbstractInteractionTask) taskConstructor.newInstance(player, wingRecipe, wingRecipe.getMaterials().getFirst().asMap(), List.of(3), 1);
		player.setInteractionTask(task);
		SielAnvilService.cancel(player, 85);
		check(player.getInteractionTask() == task && !(boolean) field(task, "finished"), "Stop cannot cancel another recipe");
		SielAnvilService.cancel(player, 84);
		check(player.getInteractionTask() == null && (boolean) field(task, "finished"), "Stop clears the accepted craft task");
		var complete = taskClass.getDeclaredMethod("onInteraction");
		complete.setAccessible(true);
		check((boolean) complete.invoke(task) && inventory.getItemByObjId(3).getItemCount() == 1, "Late completion after Stop cannot consume selected equipment");
		SielAnvilService.cancel(player, 84);
		check(inventory.getItemByObjId(3).getItemCount() == 1, "Repeated Stop does not change inventory");
		var stopPacket = new CM_SIEL_ANVIL_CANCEL(0x1FB, EnumSet.of(State.IN_GAME));
		var readStop = CM_SIEL_ANVIL_CANCEL.class.getDeclaredMethod("readImpl");
		readStop.setAccessible(true);
		stopPacket.setBuffer(ByteBuffer.wrap(HexFormat.of().parseHex("54000000")).order(ByteOrder.LITTLE_ENDIAN));
		readStop.invoke(stopPacket);
		check((boolean) field(stopPacket, "valid") && (int) field(stopPacket, "recipeId") == 84, "Stop packet carries recipe id");
		stopPacket.setBuffer(ByteBuffer.wrap(new byte[3]).order(ByteOrder.LITTLE_ENDIAN));
		readStop.invoke(stopPacket);
		check(!(boolean) field(stopPacket, "valid"), "Truncated Stop cannot cancel a task");
		int[] refundableRecipes = {1, 2, 20, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 130, 131, 140, 141, 84, 85, 90, 91, 102};
		for (int id : refundableRecipes) {
			var refundable = recipes.getRecipe(id);
			check(refundable.selectProduct(9999) == null && !refundable.getRefunds().isEmpty(), "Failure returns canonical items for recipe " + id);
		}
		byte[] request = HexFormat.of().parseHex("aa00000000000000000002006089e909040000000134df0a801a060001");
		var packet = parse(request);
		check((boolean) field(packet, "valid"), "Official request accepted");
		check(field(packet, "materials").equals(costs), "Request material ids and unsigned counts decoded");
		check((int) field(packet, "recipeId") == 170 && packet.getRemainingBytes() == 0, "Entire request consumed");
		for (int length = 0; length < request.length; length++)
			check(!(boolean) field(parse(Arrays.copyOf(request, length)), "valid"), "Truncated request " + length);
		byte[] duplicate = request.clone();
		System.arraycopy(duplicate, 12, duplicate, 20, 4);
		check(!(boolean) field(parse(duplicate), "valid"), "Duplicate ingredients rejected");
		byte[] zero = request.clone();
		Arrays.fill(zero, 16, 20, (byte) 0);
		check(!(boolean) field(parse(zero), "valid"), "Zero count rejected");
		byte[] unsupported = request.clone();
		unsupported[28] = 2;
		check((boolean) field(parse(unsupported), "valid") && (int) field(parse(unsupported), "quantity") == 2, "Batch quantity decoded");
		unsupported[28] = 0;
		check(!(boolean) field(parse(unsupported), "valid"), "Zero batch rejected");
		byte[] equipmentRequest = HexFormat.of().parseHex("54000000000000000100030000000100020000003200000001");
		check((boolean) field(parse(equipmentRequest), "valid") && field(parse(equipmentRequest), "selectedObjects").equals(List.of(3)), "Object vector parsed before ordinary materials");
		check(payload(new SM_SIEL_ANVIL_START(170, 3000)).equals("aa00000001b80b0000"), "Start matches PCAP byte for byte");
		check(payload(new SM_SIEL_ANVIL_RESULT(170, 2)).equals("aa000000010100020000"), "Result matches PCAP byte for byte");
		check(payload(new SM_SIEL_ANVIL_START(170, 2, 0)).equals("aa0000000200000000"), "Stop event uses client cancellation enum");
		check(payload(new SM_SIEL_ANVIL_RESULT(170, List.of(1, 2, 3), 1000)).equals("aa000000010300010203e803"), "Batch result byte vector and ceiling ushort");
		check(payload(new SM_UNK_01AB(Map.of(102, 1000))).equals("010066000000e80302"), "Login restores recipe ceiling progress");
		System.out.println("PASS: " + checks + " Siel Anvil checks");
	}
}
