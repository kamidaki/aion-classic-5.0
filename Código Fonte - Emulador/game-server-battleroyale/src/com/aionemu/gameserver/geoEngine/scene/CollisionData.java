package com.aionemu.gameserver.geoEngine.scene;

import com.aionemu.gameserver.geoEngine.bounding.BoundingVolume;
import com.aionemu.gameserver.geoEngine.collision.Collidable;
import com.aionemu.gameserver.geoEngine.collision.CollisionResults;
import com.aionemu.gameserver.geoEngine.math.Matrix4f;

/**
 * @author Lost Academy Team & Durak
 */
public interface CollisionData {
    public int collideWith(Collidable other,
                           Matrix4f worldMatrix,
                           BoundingVolume worldBound,
                           CollisionResults results);
}
