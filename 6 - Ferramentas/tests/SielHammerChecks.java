import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.xml.XMLConstants;
import javax.xml.bind.JAXBContext;
import javax.xml.validation.SchemaFactory;
import com.aionemu.gameserver.dataholders.*;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.*;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.SielHammerTable;
import com.aionemu.gameserver.network.aion.*;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.clientpackets.*;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.services.craft.SielHammerService;
import com.aionemu.gameserver.services.item.ItemPacketService.*;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;

/** Standalone checks against captured bytes and canonical crushing tables; no live server/database. */
class SielHammerChecks {
	private static class PacketPlayer extends Player {
		private PacketPlayer() { super(null, null); } // allocated as a shell; no world or database initialization
		@Override public int getNpcExpands() { return 0; }
		@Override public int getQuestExpands() { return 0; }
		@Override public int getItemExpands() { return 0; }
	}
	private static class RecordingKey extends java.nio.channels.SelectionKey {
		private final java.nio.channels.Selector selector;
		private int interests;
		RecordingKey(java.nio.channels.Selector selector) { this.selector = selector; }
		public java.nio.channels.SelectableChannel channel() { return null; }
		public java.nio.channels.Selector selector() { return selector; }
		public boolean isValid() { return true; }
		public void cancel() { }
		public int interestOps() { return interests; }
		public java.nio.channels.SelectionKey interestOps(int ops) { interests = ops; return this; }
		public int readyOps() { return 0; }
	}
	private static int checks;
	private static void check(boolean value, String message) {
		checks++;
		if (!value) throw new AssertionError(message);
	}
	private static Object field(Object target, String name) throws Exception {
		var f = target.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(target);
	}
	private static void set(Object target, String name, Object value) throws Exception {
		var f = target.getClass().getDeclaredField(name); f.setAccessible(true); f.set(target, value);
	}
	private static CM_SIEL_HAMMER parse(byte[] bytes) throws Exception {
		var packet = new CM_SIEL_HAMMER(0x1F5, EnumSet.of(State.IN_GAME));
		packet.setBuffer(ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN));
		var read = packet.getClass().getDeclaredMethod("readImpl"); read.setAccessible(true); read.invoke(packet);
		return packet;
	}
	private static String payload(AionServerPacket packet) throws Exception {
		var buffer = ByteBuffer.allocate(4096).order(ByteOrder.LITTLE_ENDIAN); packet.setBuf(buffer);
		var write = packet.getClass().getDeclaredMethod("writeImpl", AionConnection.class); write.setAccessible(true);
		write.invoke(packet, new Object[] { null });
		return HexFormat.of().formatHex(Arrays.copyOf(buffer.array(), buffer.position()));
	}
	private static ItemTemplate template(int id, int stack) throws Exception {
		var template = new ItemTemplate(); set(template, "itemId", id); set(template, "maxStackCount", stack); return template;
	}
	@SuppressWarnings("unchecked")
	public static void main(String[] args) throws Exception {
		// AionConnection creates an idle packet worker; terminate this standalone JVM on failure as well.
		Thread.setDefaultUncaughtExceptionHandler((thread, error) -> { error.printStackTrace(); System.exit(1); });
		Path data = Path.of(args[0]);
		var schemas = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
		var unmarshaller = JAXBContext.newInstance(SielHammerData.class).createUnmarshaller();
		unmarshaller.setSchema(schemas.newSchema(data.resolve("items/siel_hammer.xsd").toFile()));
		var hammer = (SielHammerData) unmarshaller.unmarshal(data.resolve("items/siel_hammer.xml").toFile());
		check(hammer.tableCount() == 441 && hammer.itemCount() == 4446, "All official tables and eligible items imported");
		schemas.newSchema(data.resolve("static_data.xsd").toFile()); JAXBContext.newInstance(StaticData.class);
		check(true, "Integrated schema and JAXB model");
		var factory = new com.aionemu.gameserver.network.factories.AionPacketHandlerFactory();
		var handlerField = factory.getClass().getDeclaredField("handler"); handlerField.setAccessible(true);
		var prototypes = ((AionPacketHandler) handlerField.get(factory)).getPacketsPrototypes().get(State.IN_GAME);
		check(prototypes.get(0x1F5) instanceof CM_SIEL_HAMMER && prototypes.get(0x220) instanceof CM_SIEL_HAMMER_CANCEL, "Final factory routes Hammer opcodes without replacement");
		check(prototypes.get(0x1FA) instanceof CM_SIEL_ANVIL && prototypes.get(0x1FB) instanceof CM_SIEL_ANVIL_CANCEL, "Anvil routes remain available");
		Map<Integer, SielHammerTable> tables = (Map<Integer, SielHammerTable>) field(hammer, "byId");
		for (var table : tables.values())
			for (var band : table.getBands()) {
				var distribution = new java.util.IdentityHashMap<SielHammerTable.Reward, Integer>();
				int bonuses = 0;
				for (int roll = 0; roll < 1000; roll++) {
					distribution.merge(band.selectResult(roll), 1, Integer::sum);
					if (band.hasBonus(roll)) bonuses++;
				}
				for (var result : band.getResults()) check(distribution.getOrDefault(result, 0) == result.getProbability(), "Exact weighted distribution " + table.getId());
				check(bonuses == (band.getBonus() == null ? 0 : band.getBonus().getProbability()), "Exact bonus probability " + table.getId());
				check(table.getBand(band.getMinimum()) == band && table.getBand(band.getMaximum()) == band, "Inclusive enchantment boundaries " + table.getId());
			}
		var captured = hammer.getTable(166001095);
		check(captured.getId() == 322 && captured.getKinah() == 0, "Captured L95 event stone uses free official table 322");
		check(captured.getBand(0).selectResult(999).getItemId() == 166300500 && captured.getBand(0).selectResult(0).getCount() == 1, "Captured stone yields one event essence");
		check(hammer.getTable(163000006) == null, "Official can_not_record starter arrow has no dismantling recipe");
		check(hammer.getTable(182400001) == null, "Kinah cannot be selected as a dismantling material");
		byte[] request = HexFormat.of().parseHex("010071b23fc00100000000000000");
		var packet = parse(request);
		check((boolean) field(packet, "valid") && packet.getRemainingBytes() == 0, "Official request parsed completely");
		int objectId = (int) 0xC03FB271L;
		check(field(packet, "selected").equals(Map.of(objectId, 1L)), "Unsigned object id with high bit retained");
		for (int n = 0; n < request.length; n++) check(!(boolean) field(parse(Arrays.copyOf(request, n)), "valid"), "Truncated request " + n);
		check(!(boolean) field(parse(Arrays.copyOf(request, request.length + 1)), "valid"), "Trailing garbage rejected");
		byte[] zero = request.clone(); ByteBuffer.wrap(zero).order(ByteOrder.LITTLE_ENDIAN).putLong(6, 0);
		check(!(boolean) field(parse(zero), "valid"), "Zero quantity rejected");
		ByteBuffer.wrap(zero).order(ByteOrder.LITTLE_ENDIAN).putLong(6, Long.MIN_VALUE);
		check(!(boolean) field(parse(zero), "valid"), "Unsigned quantity overflow rejected");
		ByteBuffer.wrap(zero).order(ByteOrder.LITTLE_ENDIAN).putLong(6, 1).putInt(2, 0);
		check(!(boolean) field(parse(zero), "valid"), "Zero object id rejected");
		var duplicate = ByteBuffer.allocate(26).order(ByteOrder.LITTLE_ENDIAN).putShort((short) 2).putInt(objectId).putLong(1).putInt(objectId).putLong(1).array();
		check(!(boolean) field(parse(duplicate), "valid"), "Duplicate inventory object rejected");
		var batch = ByteBuffer.allocate(242).order(ByteOrder.LITTLE_ENDIAN).putShort((short) 20);
		for (int i = 1; i <= 20; i++) batch.putInt(i).putLong(100);
		check((boolean) field(parse(batch.array()), "valid"), "Official 20 selection limit accepted");
		var oversize = ByteBuffer.allocate(254).order(ByteOrder.LITTLE_ENDIAN).putShort((short) 21);
		check(!(boolean) field(parse(oversize.array()), "valid"), "Selection above client limit rejected");
		check(payload(new SM_SIEL_HAMMER_EVENT(1, 2000)).equals("01d0070000"), "Start matches official PCAP byte for byte");
		check(payload(new SM_SIEL_HAMMER_EVENT(2, 0)).equals("0200000000"), "Stop uses client close event");
		check(payload(new SM_SIEL_HAMMER_RESULT(0, List.of(new SM_SIEL_HAMMER_RESULT.Result(166300500, 1, false))))
			.equals("000000000100548be909010000000000000000"), "Result matches official PCAP byte for byte");
		String bonus = payload(new SM_SIEL_HAMMER_RESULT(0, List.of(new SM_SIEL_HAMMER_RESULT.Result(166300500, 1000, true))));
		check(bonus.equals("000000000100548be909e80300000000000001"), "Bonus flag follows each 64-bit quantity");
		check(payload(new SM_INVENTORY_ADD_ITEM(List.of(), null, ItemAddType.CRUSH_RESULT)).equals("1201000000010000"), "Official Hammer inventory add header");
		check(payload(new SM_INVENTORY_ADD_ITEM(List.of(), null, ItemAddType.ITEM_COLLECT)).equals("0000000000000000"), "Existing inventory add header preserved");
		check(payload(new SM_DELETE_ITEM(objectId, ItemDeleteType.CRUSH)).equals("71b23fc010010000"), "Delete matches PCAP including crushing reason");
		var cubeConstructor = SM_CUBE_UPDATE.class.getDeclaredConstructor(int.class, int.class, int.class, int.class, int.class, int.class);
		cubeConstructor.setAccessible(true);
		check(payload(cubeConstructor.newInstance(0, 0, 71, 5, 1, 1)).equals("000047000000050101000000"), "Cube refresh matches complete 12-byte official S_EVENT payload");
		check(payload(SM_CUBE_UPDATE.stigmaSlots(6)).equals("0606"), "Stigma action retains its official two-byte payload");
		check(ItemDeleteType.fromUpdateType(ItemUpdateType.DEC_ITEM_CRUSH) == ItemDeleteType.CRUSH, "Full stack decrease uses crushing deletion reason");
		var stopPacket = new CM_SIEL_HAMMER_CANCEL(0x220, EnumSet.of(State.IN_GAME));
		var readStop = stopPacket.getClass().getDeclaredMethod("readImpl"); readStop.setAccessible(true);
		stopPacket.setBuffer(ByteBuffer.wrap(new byte[0])); readStop.invoke(stopPacket);
		check((boolean) field(stopPacket, "valid"), "Official empty cancel payload accepted");
		stopPacket.setBuffer(ByteBuffer.wrap(new byte[1])); readStop.invoke(stopPacket);
		check(!(boolean) field(stopPacket, "valid"), "Malformed cancel rejected");
		var inventory = new PlayerStorage(null, StorageType.CUBE);
		Item stone = new Item(objectId, template(166001095, 100), 100, false, 0); inventory.add_CharacterTransfer(stone);
		inventory.add_CharacterTransfer(new Item(2, template(166001095, 100), 10, false, 0));
		inventory.add_CharacterTransfer(new Item(3, template(166300500, 10000), 9999, false, 0));
		inventory.setLimit(3);
		var resolve = SielHammerService.class.getDeclaredMethod("resolve", Storage.class, SielHammerData.class, Map.class); resolve.setAccessible(true);
		var plan = resolve.invoke(null, inventory, hammer, Map.of(objectId, 100L));
		check(plan != null && (long) field(plan, "kinah") == 0, "Service accepts captured object id and full stack at authoritative free cost");
		check(resolve.invoke(null, inventory, hammer, Map.of(objectId, 101L)) == null, "Insufficient stack rejected");
		check(resolve.invoke(null, inventory, hammer, Map.of(objectId, Long.MAX_VALUE)) == null, "Huge tampered quantity rejected");
		check(resolve.invoke(null, inventory, hammer, Map.of(1, 1L)) == null, "Missing object rejected");
		check(resolve.invoke(null, inventory, hammer, Map.of(3, 1L)) == null, "Reward essence without crushing table rejected");
		check(resolve.invoke(null, inventory, hammer, Map.of()) == null, "Empty selection rejected");
		stone.setEquipped(true); check(resolve.invoke(null, inventory, hammer, Map.of(objectId, 1L)) == null, "Equipped material rejected"); stone.setEquipped(false);
		stone.setEnchantLevel(16); check(resolve.invoke(null, inventory, hammer, Map.of(objectId, 1L)) == null, "Enchantment outside official band rejected"); stone.setEnchantLevel(0);
		Map<Integer, SielHammerTable> eligible = (Map<Integer, SielHammerTable>) field(hammer, "byItem");
		int equipmentId = eligible.entrySet().stream().filter(e -> e.getValue().getId() == 1).findFirst().orElseThrow().getKey();
		Item equipment = new Item(4, template(equipmentId, 1), 1, false, 0); inventory.add_CharacterTransfer(equipment);
		var paidPlan = resolve.invoke(null, inventory, hammer, Map.of(4, 1L));
		check((long) field(paidPlan, "kinah") == 272000, "Official equipment cost comes from XML");
		Map<Integer, Long> both = new LinkedHashMap<>(); both.put(objectId, 100L); both.put(2, 10L);
		var batchPlan = resolve.invoke(null, inventory, hammer, both);
		check(batchPlan.equals(resolve.invoke(null, inventory, hammer, new LinkedHashMap<>(both))), "Batch snapshot stable across validation");
		var maximum = SielHammerService.class.getDeclaredMethod("maximumRewards", plan.getClass()); maximum.setAccessible(true);
		check(maximum.invoke(null, batchPlan).equals(Map.of(166300500, 110L)), "Batch sums every selected unit at official quantities");
		var itemData = new ItemData(); Map<Integer, ItemTemplate> itemMap = (Map<Integer, ItemTemplate>) field(itemData, "items");
		itemMap.put(166300500, template(166300500, 10000)); DataManager.ITEM_DATA = itemData; DataManager.SIEL_HAMMER_DATA = hammer;
		var hasRoom = SielHammerService.class.getDeclaredMethod("hasRoom", Storage.class, plan.getClass()); hasRoom.setAccessible(true);
		inventory.remove(equipment);
		check((boolean) hasRoom.invoke(null, inventory, plan), "Full inventory can use space released by consumed full stack");
		var partialPlan = resolve.invoke(null, inventory, hammer, Map.of(objectId, 2L));
		check(!(boolean) hasRoom.invoke(null, inventory, partialPlan), "Partial debit cannot count its occupied slot as free");
		var onePlan = resolve.invoke(null, inventory, hammer, Map.of(objectId, 1L));
		check((boolean) hasRoom.invoke(null, inventory, onePlan), "Existing reward stack capacity avoids unnecessary new slot");
		var roll = SielHammerService.class.getDeclaredMethod("roll", plan.getClass()); roll.setAccessible(true);
		check(roll.invoke(null, batchPlan).equals(List.of(new SM_SIEL_HAMMER_RESULT.Result(166300500, 110, false))), "Deterministic official batch result aggregates quantities");
		equipment.setEnchantLevel(10);
		inventory.add_CharacterTransfer(equipment); var upgradedPlan = resolve.invoke(null, inventory, hammer, Map.of(4, 1L));
		check(upgradedPlan != null && !upgradedPlan.equals(paidPlan), "Changed enchantment invalidates accepted snapshot");
		equipment.setEnchantLevel(11);
		check(!upgradedPlan.equals(resolve.invoke(null, inventory, hammer, Map.of(4, 1L))), "Changed enchantment within same band invalidates snapshot");
		var unsafeField = sun.misc.Unsafe.class.getDeclaredField("theUnsafe"); unsafeField.setAccessible(true);
		var unsafe = (sun.misc.Unsafe) unsafeField.get(null); var player = (Player) unsafe.allocateInstance(Player.class); set(player, "inventory", inventory);
		var taskClass = Class.forName("com.aionemu.gameserver.services.craft.SielHammerService$CrushTask");
		var constructor = taskClass.getDeclaredConstructor(Player.class, Map.class, plan.getClass()); constructor.setAccessible(true);
		var task = (AbstractInteractionTask) constructor.newInstance(player, Map.of(objectId, 100L), plan); player.setInteractionTask(task);
		SielHammerService.cancel(player);
		check(player.getInteractionTask() == null && (boolean) field(task, "finished"), "Cancel clears Hammer task");
		var complete = taskClass.getDeclaredMethod("onInteraction"); complete.setAccessible(true);
		check((boolean) complete.invoke(task) && stone.getItemCount() == 100, "Late callback after cancel cannot consume input");
		SielHammerService.cancel(player); check(stone.getItemCount() == 100, "Repeated cancel leaves input unchanged");
		var obsolete = (AbstractInteractionTask) constructor.newInstance(player, Map.of(objectId, 100L), plan);
		check((boolean) complete.invoke(obsolete) && stone.getItemCount() == 100, "Replaced task callback cannot consume input");
		AbstractInteractionTask unrelated = new AbstractInteractionTask(player, null) {
			protected boolean onInteraction() { return false; }
			protected void onInteractionFinish() { }
			protected void onInteractionStart() { }
			protected void onInteractionAbort() { throw new AssertionError("Unrelated interaction aborted"); }
		};
		player.setInteractionTask(unrelated); SielHammerService.cancel(player);
		check(player.getInteractionTask() == unrelated, "Hammer cancel cannot interrupt another system");
		// Exercise actual packet-service paths and the real connection queue without a socket or IO dispatcher.
		try (var selector = java.nio.channels.Selector.open()) {
			var recordingPlayer = (PacketPlayer) unsafe.allocateInstance(PacketPlayer.class);
			var playerInventory = Player.class.getDeclaredField("inventory"); playerInventory.setAccessible(true); playerInventory.set(recordingPlayer, inventory);
			com.aionemu.gameserver.configs.network.NetworkConfig.PACKET_PROCESSOR_MIN_THREADS = 1;
			com.aionemu.gameserver.configs.network.NetworkConfig.PACKET_PROCESSOR_MAX_THREADS = 1;
			com.aionemu.gameserver.configs.network.NetworkConfig.PACKET_PROCESSOR_THREAD_SPAWN_THRESHOLD = 1;
			com.aionemu.gameserver.configs.network.NetworkConfig.PACKET_PROCESSOR_THREAD_KILL_THRESHOLD = 1;
			var connection = (AionConnection) unsafe.allocateInstance(AionConnection.class);
			var queue = new java.util.ArrayDeque<AionServerPacket>(); set(connection, "sendMsgQueue", queue);
			for (String name : List.of("guard", "key")) {
				var f = com.aionemu.commons.network.AConnection.class.getDeclaredField(name); f.setAccessible(true);
				f.set(connection, name.equals("guard") ? new Object() : new RecordingKey(selector));
			}
			recordingPlayer.setClientConnection(connection);
			com.aionemu.gameserver.services.item.ItemPacketService.sendItemDeletePacket(recordingPlayer, StorageType.CUBE, stone, ItemDeleteType.CRUSH);
			check(queue.size() == 1 && queue.peek() instanceof SM_DELETE_ITEM, "Hammer consumption cannot refresh the cube before its result");
			com.aionemu.gameserver.utils.PacketSendUtility.sendPacket(recordingPlayer, new SM_SIEL_HAMMER_RESULT(0, List.of(new SM_SIEL_HAMMER_RESULT.Result(166300500, 1, false))));
			com.aionemu.gameserver.services.item.ItemPacketService.sendStorageUpdatePacket(recordingPlayer, StorageType.CUBE, inventory.getItemByObjId(3), ItemAddType.CRUSH_RESULT);
			check(queue.size() == 3, "Hammer reward addition defers cube refresh");
			com.aionemu.gameserver.utils.PacketSendUtility.sendPacket(recordingPlayer, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, recordingPlayer));
			check(queue.stream().map(Object::getClass).toList().equals(List.of(SM_DELETE_ITEM.class, SM_SIEL_HAMMER_RESULT.class, SM_INVENTORY_ADD_ITEM.class, SM_CUBE_UPDATE.class)), "Success ordering matches official consume/result/reward/cube sequence");
			queue.clear();
			com.aionemu.gameserver.services.item.ItemPacketService.sendItemDeletePacket(recordingPlayer, StorageType.CUBE, stone, ItemDeleteType.USE);
			check(queue.size() == 2 && queue.getLast() instanceof SM_CUBE_UPDATE, "Ordinary deletion keeps its immediate cube refresh");
			check(payload(queue.getLast()).length() == 24 && payload(queue.getLast()).endsWith("000000"), "Ordinary deletion supplies all inventory flags without changing its mode");
			queue.clear();
			com.aionemu.gameserver.services.item.ItemPacketService.sendStorageUpdatePacket(recordingPlayer, StorageType.CUBE, stone, ItemAddType.ITEM_COLLECT);
			check(queue.size() == 2 && queue.getLast() instanceof SM_CUBE_UPDATE, "Ordinary additions keep their immediate cube refresh");
			check(payload(queue.getLast()).length() == 24 && payload(queue.getLast()).endsWith("000000"), "Ordinary addition supplies all inventory flags without changing its mode");
			queue.clear();
			var cancelledTask = (AbstractInteractionTask) constructor.newInstance(recordingPlayer, Map.of(objectId, 100L), plan); recordingPlayer.setInteractionTask(cancelledTask);
			SielHammerService.cancel(recordingPlayer);
			check(queue.size() == 1 && queue.peek() instanceof SM_SIEL_HAMMER_EVENT && payload(queue.peek()).equals("0200000000"), "Real cancellation still sends its close event");
			complete.invoke(cancelledTask); SielHammerService.cancel(recordingPlayer);
			check(queue.size() == 1 && stone.getItemCount() == 100, "Late completion and repeated close add no success/cancellation packets or debit");
		}
		System.out.println("PASS: " + checks + " Siel Hammer checks");
		System.exit(0); // no packets were submitted to AionConnection's idle worker
	}
}
