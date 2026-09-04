package com.aionemu.commons.utils.xml;

import com.aionemu.commons.utils.xml.StringSchemaOutputResolver;
import com.aionemu.commons.utils.xml.XmlUtils;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.Writer;
import java.net.URL;
import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import javax.xml.bind.SchemaOutputResolver;
import javax.xml.bind.Unmarshaller;
import javax.xml.validation.Schema;
import org.w3c.dom.Document;

public class JAXBUtil {
    public static String serialize(Object obj) {
        try {
            JAXBContext jc = JAXBContext.newInstance((Class[])new Class[]{obj.getClass()});
            Marshaller m = jc.createMarshaller();
            m.setProperty("jaxb.encoding", (Object)"UTF-8");
            m.setProperty("jaxb.formatted.output", (Object)true);
            StringWriter sw = new StringWriter();
            m.marshal(obj, (Writer)sw);
            return sw.toString();
        }
        catch (JAXBException e) {
            throw new RuntimeException("Failed to marshall object of class " + obj.getClass().getName(), e);
        }
    }

    public static Document serializeToDocument(Object obj) {
        String s = JAXBUtil.serialize(obj);
        return XmlUtils.getDocument(s);
    }

    public static <T> T deserialize(String s, Class<T> clazz) {
        return JAXBUtil.deserialize(s, clazz, (Schema)null);
    }

    public static <T> T deserialize(String s, Class<T> clazz, URL schemaURL) {
        Schema schema = XmlUtils.getSchema(schemaURL);
        return JAXBUtil.deserialize(s, clazz, schema);
    }

    public static <T> T deserialize(String s, Class<T> clazz, String schemaString) {
        Schema schema = XmlUtils.getSchema(schemaString);
        return JAXBUtil.deserialize(s, clazz, schema);
    }

    public static <T> T deserialize(Document xml, Class<T> clazz, String schemaString) {
        String xmlAsString = XmlUtils.getString(xml);
        return JAXBUtil.deserialize(xmlAsString, clazz, schemaString);
    }

    public static <T> T deserialize(String s, Class<T> clazz, Schema schema) {
        try {
            JAXBContext jc = JAXBContext.newInstance((Class[])new Class[]{clazz});
            Unmarshaller u = jc.createUnmarshaller();
            u.setSchema(schema);
            return (T)u.unmarshal((Reader)new StringReader(s));
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to unmarshall class " + clazz.getName() + " from xml:\n " + s, e);
        }
    }

    public static String generateSchemma(Class<?> ... classes) {
        try {
            JAXBContext jc = JAXBContext.newInstance((Class[])classes);
            StringSchemaOutputResolver ssor = new StringSchemaOutputResolver();
            jc.generateSchema((SchemaOutputResolver)ssor);
            return ssor.getSchemma();
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to generate schemma", e);
        }
    }
}

