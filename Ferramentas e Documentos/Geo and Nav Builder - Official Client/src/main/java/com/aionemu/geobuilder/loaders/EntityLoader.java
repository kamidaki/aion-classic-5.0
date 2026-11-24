package com.aionemu.geobuilder.loaders;

import com.aionemu.geobuilder.entries.*;
import com.aionemu.geobuilder.utils.PathSanitizer;
import com.aionemu.geobuilder.utils.Vector3;
import com.aionemu.geobuilder.utils.XmlParser;
import org.jdom2.Document;
import org.jdom2.Element;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class EntityLoader {

  private EntityLoader() {
  }

  public static List<EntityEntry> loadPlaceables(ByteBuffer mission, Map<String, Short> addresses) throws Exception {
    Document document = XmlParser.parse(mission);
    Element rootNode = document.getRootElement();
    Element objectsNode = rootNode.getChild("Objects");
    List<Element> entities = objectsNode != null ? objectsNode.getChildren("Entity") : Collections.emptyList();
    List<EntityEntry> entityEntries = new ArrayList<>(entities.size());
    for (Element node : entities) {
      String entityClass = node.getAttributeValue("EntityClass");
      if ("Door".equalsIgnoreCase(entityClass)) {
        Element prop = node.getChild("Properties");
        if (prop != null && prop.getAttributeValue("object_AnimatedModel") != null && !prop.getAttributeValue("object_AnimatedModel").isEmpty()) {
          DoorEntry entry = new DoorEntry();
          DoorEntry entry2 = new DoorEntry();
          entry.entityId = XmlParser.parseSafeInt(node, "EntityId", 0);
          entry2.entityId = entry.entityId;
          loadNameAnglePositionAndScale(node, entry);
          entry2.name = entry.name;
          entry2.angle = entry.angle;
          entry2.pos = entry.pos;
          entry2.scale = entry.scale;
          String mesh = PathSanitizer.sanitize(prop.getAttributeValue("object_AnimatedModel"));
          entry.mesh = mesh;
          entry2.mesh = mesh;
          entry2.suffix = "_state2";
          entry.type = EntryType.DOOR;
          entry2.type = EntryType.DOOR2;
          entityEntries.add(entry);
          entityEntries.add(entry2);
        }
      } else if ("PlaceableObject".equalsIgnoreCase(entityClass)
                           || "AbyssArtifacts".equalsIgnoreCase(entityClass)
                           || "AbyssShield".equalsIgnoreCase(entityClass)
                           || "AbyssDoor".equalsIgnoreCase(entityClass)
                           || "tailoring".equalsIgnoreCase(entityClass)
                           || "weapon_craft".equalsIgnoreCase(entityClass)
                           || "handiwork".equalsIgnoreCase(entityClass)
                           || "armor_craft".equalsIgnoreCase(entityClass)
                           || "menuisier".equalsIgnoreCase(entityClass)
                           || "alchemy".equalsIgnoreCase(entityClass)
                           || "cooking".equalsIgnoreCase(entityClass)) {
        Element prop = node.getChild("Properties");
        if (prop != null && prop.getAttributeValue("fileLadderCGF") != null 
            && !prop.getAttributeValue("fileLadderCGF").isEmpty() 
            && !prop.getAttributeValue("fileLadderCGF").endsWith(".saf")) {
          EntityEntry entry = new EntityEntry();
          entry.entityId = XmlParser.parseSafeInt(node, "EntityId", 0); // static id
          loadNameAnglePositionAndScale(node, entry);
          entry.mesh = PathSanitizer.sanitize(prop.getAttributeValue("fileLadderCGF"));
          entry.type = EntryType.PLACEABLE;
          entityEntries.add(entry);
        }
      } else if ("BasicEntity".equalsIgnoreCase(entityClass)) {
        Element prop = node.getChild("Properties");
        if (prop != null && prop.getAttributeValue("object_Model") != null 
            && !prop.getAttributeValue("object_Model").isEmpty() 
            && !prop.getAttributeValue("object_Model").endsWith(".saf")) {
          EntityEntry entry = new EntityEntry();
          entry.mesh = PathSanitizer.sanitize(prop.getAttributeValue("object_Model"));
          if (entry.mesh.endsWith(".cga")) {
            // TODO: check if there are cgas we should not ignore.
            continue;
          }
          entry.entityId = 0; // basic entities have a static id but they are always spawned, so serverside spawning is not needed
          loadNameAnglePositionAndScale(node, entry);
          String eventType = node.getAttributeValue("EventType");
          if (eventType != null && !eventType.isEmpty()) {
            entry.entityId = AionEventRegistry.resolveEventId(eventType, entry);
            entry.type = EntryType.EVENT;
            BrushLstLoader.EVENT_MESHES.add(entry.mesh);
          }
          entityEntries.add(entry);
        }
      } else if ("TownObject".equalsIgnoreCase(entityClass)) {
        Element prop = node.getChild("Properties");
        if (prop != null && prop.getAttributeValue("object_Model") != null 
            && !prop.getAttributeValue("object_Model").isEmpty() 
            && !prop.getAttributeValue("object_Model").endsWith(".saf")) {
          TownEntry entry = new TownEntry();
          entry.entityId = XmlParser.parseSafeInt(node, "EntityId", 0); // static id
          loadNameAnglePositionAndScale(node, entry);
          entry.level = XmlParser.parseSafeInt(prop, "Level", 0);
          entry.townId = XmlParser.parseSafeInt(prop, "TownID", 0);
          entry.mesh = PathSanitizer.sanitize(prop.getAttributeValue("object_Model"));
          entityEntries.add(entry);
        }
      } else if ("HousingBuilding".equalsIgnoreCase(entityClass)) {
        Element prop = node.getChild("Properties");
        if (prop != null) {
          HouseEntry entry = new HouseEntry();
          entry.entityId = XmlParser.parseSafeInt(node, "EntityId", 0); // static id
          loadNameAnglePositionAndScale(node, entry);
          String addressName = prop.getAttributeValue("address_Address");
          entry.address = (addressName == null || addressName.isEmpty()) ? -1 : addresses.getOrDefault(addressName, (short) -1);

          Element partsInfo = prop.getChild("PartsInfo");
          if (partsInfo != null) {
            Element build = partsInfo.getChild("Build");
            Element land = partsInfo.getChild("Land");
            if (land != null) {
              String housingobjFence = land.getAttributeValue("housingobjFence");
              if (housingobjFence != null && !housingobjFence.isEmpty()) {
                entry.meshes.add(PathSanitizer.sanitize(housingobjFence));
              }

              String housingobjGarden = land.getAttributeValue("housingobjGarden");
              if (housingobjGarden != null && !housingobjGarden.isEmpty()) {
                entry.meshes.add(PathSanitizer.sanitize(housingobjGarden));
              }
            }

            if (build != null) {
              Element buildInfo = prop.getChild("BuildInfo");
              if (buildInfo != null && buildInfo.getAttribute("vectorBuild_Offset") != null) {
                String offsetString = buildInfo.getAttributeValue("vectorBuild_Offset");
                if (offsetString != null && !offsetString.isEmpty()) {
                  String[] offsetSplitted = offsetString.split(",");
                  if (offsetSplitted.length == 3) {
                    float xOffset = Float.parseFloat(offsetSplitted[0]);
                    float yOffset = Float.parseFloat(offsetSplitted[1]);
                    float zOffset = Float.parseFloat(offsetSplitted[2]);
                    if (xOffset != 0f || yOffset != 0f || zOffset != 0f) {
                      entityEntries.add(entry);
                      HouseEntry entry2 = new HouseEntry();
                      entry2.entityId = entry.entityId;
                      entry2.name = entry.name;
                      entry2.angle = entry.angle;
                      entry2.pos = entry.pos;
                      entry2.scale = entry.scale;
                      entry2.address = entry.address;
                      Vector3 offset = Vector3.transform(new Vector3(xOffset, yOffset, zOffset), entry2.getMatrix());
                      entry2.pos = new Vector3(entry2.pos.x + offset.x, entry2.pos.y + offset.y, entry2.pos.z + offset.z);
                      entry = entry2;
                    }
                  }
                }
              }
              String housingobjDoor = build.getAttributeValue("housingobjDoor");
              if (housingobjDoor != null && !housingobjDoor.isEmpty()) {
                entry.mesh = PathSanitizer.sanitize(housingobjDoor);
                entry.meshes.add(entry.mesh);
              }

              String housingobjFrame = build.getAttributeValue("housingobjFrame");
              if (housingobjFrame != null && !housingobjFrame.isEmpty()) {
                entry.meshes.add(PathSanitizer.sanitize(housingobjFrame));
              }

              String housingobjOutWall = build.getAttributeValue("housingobjOutWall");
              if (housingobjOutWall != null && !housingobjOutWall.isEmpty()) {
                entry.meshes.add(PathSanitizer.sanitize(housingobjOutWall));
              }

              String housingobjRoof = build.getAttributeValue("housingobjRoof");
              if (housingobjRoof != null && !housingobjRoof.isEmpty()) {
                entry.meshes.add(PathSanitizer.sanitize(housingobjRoof));
              }

              for (int i = 1; i <= 5; i++) {
                String housingobjInFloor = build.getAttributeValue("housingobjInFloor" + i);
                if (housingobjInFloor != null && !housingobjInFloor.isEmpty()) {
                  entry.meshes.add(PathSanitizer.sanitize(housingobjInFloor));
                }

                String housingobjInWall = build.getAttributeValue("housingobjInWall" + i);
                if (housingobjInWall != null && !housingobjInWall.isEmpty()) {
                  entry.meshes.add(PathSanitizer.sanitize(housingobjInWall));
                }
              }
            }
            entityEntries.add(entry);
          }
        }
      }
    }
    return entityEntries;
  }

  private static void loadNameAnglePositionAndScale(Element node, EntityEntry entry) {
    entry.name = node.getAttributeValue("Name");
    entry.angle = new Vector3();
    String angles = node.getAttributeValue("Angles");
    if (angles != null) {
      String[] values = angles.split(",");
      if (values.length == 3) {
        try {
          entry.angle.x = Float.parseFloat(values[0]);
          entry.angle.y = Float.parseFloat(values[1]);
          entry.angle.z = Float.parseFloat(values[2]);
        } catch (NumberFormatException e) {
          // ignore
        }
      }
    }
    entry.pos = new Vector3();
    String pos = node.getAttributeValue("Pos");
    if (pos != null) {
      String[] posValues = pos.split(",");
      if (posValues.length == 3) {
        try {
          entry.pos.x = Float.parseFloat(posValues[0]);
          entry.pos.y = Float.parseFloat(posValues[1]);
          entry.pos.z = Float.parseFloat(posValues[2]);
        } catch (NumberFormatException e) {
          // ignore
        }
      }
    }

    entry.scale = new Vector3(1, 1, 1);
    String scales = node.getAttributeValue("Scale");
    if (scales != null) {
      String[] scaleValues = scales.split(",");
      if (scaleValues.length == 3) {
        try {
          entry.scale.x = Float.parseFloat(scaleValues[0]);
          entry.scale.y = Float.parseFloat(scaleValues[1]);
          entry.scale.z = Float.parseFloat(scaleValues[2]);
        } catch (NumberFormatException e) {
          // ignore
        }
      }
    }
  }
}
