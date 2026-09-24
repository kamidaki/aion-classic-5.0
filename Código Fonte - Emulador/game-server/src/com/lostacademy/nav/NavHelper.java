package com.lostacademy.nav;

import java.util.ArrayList;
import java.util.HashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.geoEngine.scene.NavGeometry;
import com.lostacademy.nav.NavService.NavPathway;

/**
 * Implements a pathfinding algorithm similar to A* to traverse through {@link NavGeometry}.
 *
 * @author Yon (Aion Reconstruction Project)
 */
class NavHelper {

	private final Logger LOG = LoggerFactory.getLogger(NavHelper.class);

	public final static float ARBITRARY_SMALL_VALUE = 5;
	public final static int ARBITRARY_LARGE_VALUE = 800;
	public final static float PATH_WEIGHT = 0.2F;
	public final static float TARGET_WEIGHT = 20;

	private static final class NavHeapNode implements Comparable<NavHeapNode> {
		boolean open = false;
		NavGeometry tile;
		NavHeapNode parent;
		int heapIndex;
		float pathCost, targetDist;

		NavHeapNode(NavGeometry node, float x2, float y2, float z2, NavGeometry endTile, float targetWeight) {
			this.tile = node;
			if (tile == endTile) {
				targetDist = 0;
			} else {
				targetDist = node.getPriority(x2, y2, z2) * targetWeight;
			}
		}

		NavHeapNode(NavGeometry node, NavHeapNode parent, boolean useWeight, float x2, float y2, float z2, NavGeometry endTile, float targetWeight, float pathWeight) {
			this(node, x2, y2, z2, endTile, targetWeight);
			this.parent = parent;
			float basePriority = parent.pathCost + parent.tile.getInRad();
			if (useWeight) {
				pathCost = basePriority + basePriority * pathWeight;
			} else {
				pathCost = basePriority;
			}
		}

		void checkAndUpdateParent(NavHeapNode newParent, boolean useWeight, float pathWeight, java.util.function.Consumer<NavHeapNode> onUpdate) {
			if (newParent == null || parent == null || newParent.parent == this) return;
			if (parent.pathCost > newParent.pathCost) {
				parent = newParent;
				if (useWeight) {
					pathCost = parent.pathCost + parent.tile.getInRad();
					pathCost += pathCost * pathWeight;
				} else {
					pathCost = parent.pathCost + parent.tile.getInRad();
				}
				onUpdate.accept(this);
			}
		}

		float getPriority() {
			return pathCost + targetDist;
		}

		void open(NavHelper context) {
			if (open) return;
			float[] vec = {context.x2, context.y2};

			if (tile.getEdge1() != null) {
				NavGeometry edge1 = tile.getEdge1();
				if (!context.contains(edge1)) {
					NavHeapNode newNode = new NavHeapNode(edge1, this, !tile.isTowardsEdge((byte) 1, vec),
						context.x2, context.y2, context.z2, context.endTile, TARGET_WEIGHT, PATH_WEIGHT);
					context.add(newNode);
				} else {
					NavHeapNode child = context.getNode(edge1);
					if (child != parent) child.checkAndUpdateParent(this, !tile.isTowardsEdge((byte) 1, vec), PATH_WEIGHT, context::onUpdateNode);
				}
			}

			if (tile.getEdge2() != null) {
				NavGeometry edge2 = tile.getEdge2();
				if (!context.contains(edge2)) {
					NavHeapNode newNode = new NavHeapNode(edge2, this, !tile.isTowardsEdge((byte) 2, vec),
						context.x2, context.y2, context.z2, context.endTile, TARGET_WEIGHT, PATH_WEIGHT);
					context.add(newNode);
				} else {
					NavHeapNode child = context.getNode(edge2);
					if (child != parent) child.checkAndUpdateParent(this, !tile.isTowardsEdge((byte) 2, vec), PATH_WEIGHT, context::onUpdateNode);
				}
			}

			if (tile.getEdge3() != null) {
				NavGeometry edge3 = tile.getEdge3();
				if (!context.contains(edge3)) {
					NavHeapNode newNode = new NavHeapNode(edge3, this, !tile.isTowardsEdge((byte) 3, vec),
						context.x2, context.y2, context.z2, context.endTile, TARGET_WEIGHT, PATH_WEIGHT);
					context.add(newNode);
				} else {
					NavHeapNode child = context.getNode(edge3);
					if (child != parent) child.checkAndUpdateParent(this, !tile.isTowardsEdge((byte) 3, vec), PATH_WEIGHT, context::onUpdateNode);
				}
			}
			open = true;
		}

		@Override
		public int compareTo(NavHeapNode other) {
			float pThis = getPriority();
			float pOther = other.getPriority();
			if (pThis > pOther) return 1;
			if (pThis < pOther) return -1;
			if (targetDist > other.targetDist) return 1;
			if (targetDist < other.targetDist) return -1;
			return 0;
		}
	}

	final float x1, y1, z1;
	final float x2, y2, z2;
	NavGeometry endTile;
	private HashMap<NavGeometry, NavHeapNode> list;
	private NavHeapNode[] heap;
	private int currentHeapCount = 0;

	NavHelper(NavGeometry startTile, NavGeometry endTile, float x1, float y1, float z1, float x2, float y2, float z2) {
		assert startTile != null;
		heap = new NavHeapNode[128];
		list = new HashMap<>(256);
		this.endTile = endTile;
		this.x1 = x1; this.y1 = y1; this.z1 = z1;
		this.x2 = x2; this.y2 = y2; this.z2 = z2;
		init(startTile);
	}

	private void init(NavGeometry tile) {
		NavHeapNode startNode = new NavHeapNode(tile, x2, y2, z2, endTile, TARGET_WEIGHT);
		add(startNode);
	}

	public void destroy() {
		for (NavGeometry key : list.keySet()) {
			list.get(key).parent = null;
		}
		list.clear();
	}

	public NavPathway[] createPathway() {
		boolean finished = false;
		if (endTile == null) {
			NavHeapNode current;
			short opCount = 0;
			do {
				current = removeFirst();
				if (current.targetDist < ARBITRARY_SMALL_VALUE * TARGET_WEIGHT) {
					finished = true;
					break;
				}
				current.open(this);
				if (opCount++ > ARBITRARY_LARGE_VALUE) break;
			} while (currentHeapCount > 0);
			if (finished) return retrace(current);
		} else {
			NavHeapNode current;
			short opCount = 0;
			do {
				current = removeFirst();
				if (current.tile == endTile) {
					finished = true;
					break;
				}
				current.open(this);
				if (opCount++ > ARBITRARY_LARGE_VALUE) break;
			} while (currentHeapCount > 0);
			if (finished) return retrace(current);
		}
		return new NavPathway[0];
	}

	private NavPathway[] retrace(NavHeapNode node) {
		ArrayList<NavPathway> ret = new ArrayList<NavPathway>();
		NavHeapNode child = node;
		NavHeapNode parent = node;
		while (parent.parent != null) {
			parent = parent.parent;
			assert parent.parent == null || parent.parent != child : "Parent of parent node is child node! Infinite Loop!";
			NavPathway port;
			if (parent.tile.getEdge1() == child.tile) {
				port = new NavPathway(parent.tile, (byte) 1);
			} else if (parent.tile.getEdge2() == child.tile) {
				port = new NavPathway(parent.tile, (byte) 2);
			} else {
				assert parent.tile.getEdge3() == child.tile;
				port = new NavPathway(parent.tile, (byte) 3);
			}
			ret.add(port);
			if (ret.size() > ARBITRARY_LARGE_VALUE) {
				LOG.error("Retracing path produced too many portals: (" + x1 + ", " + y1 + ", " + z1 + ") --> (" + x2 + ", " + y2 + ", " + z2 + ")");
				return new NavPathway[0];
			}
			child = parent;
		}
		return ret.toArray(new NavPathway[0]);
	}

	private void add(NavHeapNode node) {
		list.put(node.tile, node);
		node.heapIndex = currentHeapCount;
		heap[currentHeapCount++] = node;
		if (currentHeapCount == heap.length) {
			NavHeapNode[] tempHeap = new NavHeapNode[heap.length + 50];
			System.arraycopy(heap, 0, tempHeap, 0, currentHeapCount);
			heap = tempHeap;
		}
		sortUp(node);
	}

	private boolean contains(NavGeometry tile) {
		return list.containsKey(tile);
	}

	private NavHeapNode getNode(NavGeometry tile) {
		return list.get(tile);
	}

	private NavHeapNode removeFirst() {
		if (currentHeapCount == 0) return null;
		NavHeapNode ret = heap[0];
		currentHeapCount--;
		heap[0] = heap[currentHeapCount];
		heap[0].heapIndex = 0;
		sortDown(heap[0]);
		return ret;
	}

	private void onUpdateNode(NavHeapNode node) {
		if (node.open) return;
		sortUp(node);
		sortDown(node);
	}

	private void sortDown(NavHeapNode node) {
		do {
			int ciLeft = node.heapIndex * 2 + 1;
			int ciRight = node.heapIndex * 2 + 2;
			int swapIndex;
			if (ciLeft < currentHeapCount) {
				swapIndex = ciLeft;
				if (ciRight < currentHeapCount) {
					if (heap[ciRight].compareTo(heap[ciLeft]) < 0) {
						swapIndex = ciRight;
					}
				}
				if (node.compareTo(heap[swapIndex]) > 0) {
					swap(node, heap[swapIndex]);
				} else {
					break;
				}
			} else {
				break;
			}
		} while (true);
	}

	private void sortUp(NavHeapNode node) {
		int pi;
		do {
			pi = (node.heapIndex - 1) / 2;
			if (heap[pi].compareTo(node) > 0) {
				swap(heap[pi], node);
			} else {
				break;
			}
		} while (true);
	}

	private void swap(NavHeapNode node1, NavHeapNode node2) {
		heap[node1.heapIndex] = node2;
		heap[node2.heapIndex] = node1;
		int heapIndex1 = node1.heapIndex;
		node1.heapIndex = node2.heapIndex;
		node2.heapIndex = heapIndex1;
	}
}