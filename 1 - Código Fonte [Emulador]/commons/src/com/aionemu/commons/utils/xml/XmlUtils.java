package com.aionemu.commons.utils.xml;

import java.io.StringReader;
import java.io.StringWriter;
import java.net.URL;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;

public abstract class XmlUtils {
    private static final DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
    private static final TransformerFactory tf = TransformerFactory.newInstance();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static Document getDocument(String xmlSource) {
        Class<XmlUtils> clazz = XmlUtils.class;
        synchronized (XmlUtils.class) {
            Document document = null;
            if (xmlSource != null) {
                try {
                    StringReader stream = new StringReader(xmlSource);
                    DocumentBuilder db = dbf.newDocumentBuilder();
                    document = db.parse(new InputSource(stream));
                }
                catch (Exception e) {
                    throw new RuntimeException("Error converting string to document", e);
                }
            }
            // ** MonitorExit[var1_1] (shouldn't be in output)
            return document;
        }
    }

    public static String getString(Document document) {
        Class<XmlUtils> clazz = XmlUtils.class;
        synchronized (XmlUtils.class) {
            try {
                DOMSource domSource = new DOMSource(document);
                StringWriter writer = new StringWriter();
                StreamResult result = new StreamResult(writer);
                Transformer transformer = tf.newTransformer();
                transformer.transform(domSource, result);
                // ** MonitorExit[var1_1] (shouldn't be in output)
                return writer.toString();
            }
            catch (TransformerException e) {
                throw new RuntimeException(e);
            }
        }
    }

    public static Schema getSchema(String schemaString) {
        Schema schema = null;
        try {
            if (schemaString != null) {
                SchemaFactory sf = SchemaFactory.newInstance("http://www.w3.org/2001/XMLSchema");
                StreamSource ss = new StreamSource();
                ss.setReader(new StringReader(schemaString));
                schema = sf.newSchema(ss);
            }
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to create schemma from string: " + schemaString, e);
        }
        return schema;
    }

    public static Schema getSchema(URL schemaURL) {
        Schema schema = null;
        try {
            if (schemaURL != null) {
                SchemaFactory sf = SchemaFactory.newInstance("http://www.w3.org/2001/XMLSchema");
                schema = sf.newSchema(schemaURL);
            }
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to create shcemma from URL " + schemaURL, e);
        }
        return schema;
    }

    public static void validate(Schema schema, Document document) {
        Validator validator = schema.newValidator();
        try {
            validator.validate(new DOMSource(document));
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to validate document", e);
        }
    }

    static {
        dbf.setNamespaceAware(true);
    }
}

