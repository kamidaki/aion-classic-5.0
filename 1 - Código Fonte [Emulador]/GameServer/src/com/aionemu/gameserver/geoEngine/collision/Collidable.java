package com.aionemu.gameserver.geoEngine.collision;

/**
 * Interface for collidable objects.
 */
public interface Collidable {

    /**
     * Check collision with another collidable
     * @param other
     * @param results
     * @return how many collisions were found
     */
    public int collideWith(Collidable other, CollisionResults results) throws UnsupportedCollisionException;
}
