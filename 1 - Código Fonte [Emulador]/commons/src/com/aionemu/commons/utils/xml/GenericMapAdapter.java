package com.aionemu.commons.utils.xml;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.adapters.XmlAdapter;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;

public class GenericMapAdapter<K, V>
extends XmlAdapter<GenericMapAdapter.KeyValuePairContainer<K, V>, Map<K, V>> {
    public KeyValuePairContainer<K, V> marshal(Map<K, V> v) throws Exception {
        if (v == null) {
            return null;
        }
        KeyValuePairContainer<K, V> result = new KeyValuePairContainer<K, V>();
        for (Map.Entry<K, V> entry : v.entrySet()) {
            result.addElement(entry);
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    public Map<K, V> unmarshal(KeyValuePairContainer<K, V> v) throws Exception {
        HashMap<K, V> result = new HashMap<K, V>();
        for (KeyValuePair<K, V> kvp : v.getValues()) {
            if (kvp.getMapValue() != null) {
                result.put(kvp.getKey(), (V)kvp.getMapValue());
                continue;
            }
            if (kvp.getCollectionValue() != null) {
                result.put(kvp.getKey(), (V)kvp.getCollectionValue());
                continue;
            }
            result.put(kvp.getKey(), kvp.getValue());
        }
        return result;
    }

    @XmlRootElement
    @XmlAccessorType(value=XmlAccessType.NONE)
    public static class KeyValuePair<K, V> {
        @XmlElement
        private K key;
        @XmlElement
        private V value;
        @XmlElement
        private Collection collectionValue;
        @XmlElement
        @XmlJavaTypeAdapter(value=GenericMapAdapter.class)
        private Map mapValue;

        public KeyValuePair() {
        }

        public KeyValuePair(Map.Entry<K, V> entry) {
            this(entry.getKey(), entry.getValue());
        }

        public KeyValuePair(K key, V value) {
            this.key = key;
            if (value instanceof Collection) {
                this.collectionValue = (Collection)value;
            } else if (value instanceof Map) {
                this.mapValue = (Map)value;
            } else {
                this.value = value;
            }
        }

        public K getKey() {
            return this.key;
        }

        public V getValue() {
            return this.value;
        }

        public Collection getCollectionValue() {
            return this.collectionValue;
        }

        public Map getMapValue() {
            return this.mapValue;
        }
    }

    @XmlRootElement
    @XmlAccessorType(value=XmlAccessType.NONE)
    public static class KeyValuePairContainer<K, V> {
        @XmlElement(name="mapEntry")
        private List<KeyValuePair<K, V>> values;

        public void addElement(Map.Entry<K, V> entry) {
            if (this.values == null) {
                this.values = new ArrayList<KeyValuePair<K, V>>();
            }
            this.values.add(new KeyValuePair<K, V>(entry));
        }

        public List<KeyValuePair<K, V>> getValues() {
            if (this.values == null) {
                return Collections.emptyList();
            }
            return this.values;
        }
    }
}

