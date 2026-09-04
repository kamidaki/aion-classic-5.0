package com.aionemu.commons.scripting.impl;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.configs.CommonsConfig;
import com.aionemu.commons.scripting.CompilationResult;
import com.aionemu.commons.scripting.ScriptCompiler;
import com.aionemu.commons.scripting.ScriptCompilerCache;
import com.aionemu.commons.scripting.ScriptContext;
import com.aionemu.commons.scripting.classlistener.ClassListener;
import com.aionemu.commons.scripting.impl.javacompiler.ScriptCompilerImpl;

/**
 * Implementation of {@link ScriptContext} supporting both single-root with parent/child hierarchies
 * and multi-root directory scanning, fully compatible with Java 25.
 * 
 */
public class ScriptContextImpl implements ScriptContext {

	private static final Logger log = LoggerFactory.getLogger(ScriptContextImpl.class);

	private final ScriptContext parentScriptContext;
	private final File root;
	private final File[] directories;

	private Iterable<File> libraries;
	private Set<ScriptContext> childScriptContexts;
	private CompilationResult compilationResult;
	private ClassListener classListener;
	private String compilerClassName;

	public ScriptContextImpl(File root) {
		this(root, null);
	}

	public ScriptContextImpl(File root, ScriptContext parent) {
		if (root == null) {
			throw new NullPointerException("Root file must be specified");
		}
		if (!root.exists() || !root.isDirectory()) {
			throw new IllegalArgumentException("Root directory does not exist or is not a directory: " + root);
		}
		this.root = root;
		this.directories = new File[]{root};
		this.parentScriptContext = parent;
	}

	public ScriptContextImpl(File... directories) {
		if (directories.length == 0 || !Stream.of(directories).allMatch(File::isDirectory)) {
			throw new IllegalArgumentException("Invalid directories given: " + Arrays.toString(directories));
		}
		this.root = directories[0];
		this.directories = directories;
		this.parentScriptContext = null;
	}

	@Override
	public synchronized void init() {
		if (compilationResult != null) {
			log.error("Init request on initialized ScriptContext");
			return;
		}

		ScriptCompiler scriptCompiler = instantiateCompiler();
		if (parentScriptContext != null && parentScriptContext.getCompilationResult() != null) {
			scriptCompiler.setParentClassLoader(parentScriptContext.getCompilationResult().getClassLoader());
		}
		if (libraries != null) {
			scriptCompiler.setLibraries(libraries);
		}

		List<File> sourceFiles = findFiles();
		if (CommonsConfig.SCRIPT_COMPILER_CACHING) {
			scriptCompiler.setClasses(ScriptCompilerCache.findValidCachedClassFiles(sourceFiles));
		}

		try {
			compilationResult = scriptCompiler.compile(sourceFiles);
		} catch (ClassFormatError e) {
			if (!CommonsConfig.SCRIPT_COMPILER_CACHING) {
				throw e;
			}
			log.warn("Couldn't load cached classes from " + ScriptCompilerCache.CACHE_DIR + ", refreshing files in cache...", e);
			ScriptCompilerCache.invalidate(sourceFiles = findFiles());
			scriptCompiler.setClasses(Collections.emptyMap());
			compilationResult = scriptCompiler.compile(sourceFiles);
		}

		if (CommonsConfig.SCRIPT_COMPILER_CACHING) {
			ScriptCompilerCache.cacheClasses(compilationResult.getBinaryClasses());
		}

		ClassListener cl = getClassListener();
		if (cl != null) {
			cl.postLoad(compilationResult.getCompiledClasses());
		}

		if (childScriptContexts != null) {
			for (ScriptContext child : childScriptContexts) {
				child.init();
			}
		}
	}

	protected ScriptCompiler instantiateCompiler() {
		if (compilerClassName != null) {
			try {
				Class<?> clazz = Class.forName(compilerClassName);
				return (ScriptCompiler) clazz.getDeclaredConstructor().newInstance();
			} catch (Exception e) {
				log.error("Failed to instantiate compiler: " + compilerClassName + ", using default", e);
			}
		}
		return new ScriptCompilerImpl();
	}

	private List<File> findFiles() {
		List<File> files = new ArrayList<>();
		for (File dir : directories) {
			if (!dir.exists() || !dir.isDirectory()) {
				continue;
			}
			try (var paths = Files.find(dir.toPath(), Integer.MAX_VALUE, (path, attrs) -> attrs.isRegularFile() && path.toString().endsWith(".java"))) {
				paths.forEach(path -> files.add(path.toFile()));
			} catch (IOException e) {
				throw new RuntimeException("Error scanning " + dir, e);
			}
		}
		return files;
	}

	@Override
	public synchronized void shutdown() {
		if (compilationResult == null) {
			log.error("Shutdown of not initialized script context", new Exception());
			return;
		}
		if (childScriptContexts != null) {
			for (ScriptContext child : childScriptContexts) {
				child.shutdown();
			}
		}
		ClassListener cl = getClassListener();
		if (cl != null) {
			cl.preUnload(compilationResult.getCompiledClasses());
		}
		compilationResult = null;
	}

	@Override
	public void reload() {
		shutdown();
		init();
	}

	@Override
	public File getRoot() {
		return root;
	}

	@Override
	public CompilationResult getCompilationResult() {
		return compilationResult;
	}

	@Override
	public synchronized boolean isInitialized() {
		return compilationResult != null;
	}

	@Override
	public void setLibraries(Iterable<File> files) {
		this.libraries = files;
	}

	@Override
	public Iterable<File> getLibraries() {
		return libraries;
	}

	@Override
	public ScriptContext getParentScriptContext() {
		return parentScriptContext;
	}

	@Override
	public Collection<ScriptContext> getChildScriptContexts() {
		return childScriptContexts;
	}

	@Override
	public synchronized void addChildScriptContext(ScriptContext context) {
		if (childScriptContexts == null) {
			childScriptContexts = new HashSet<>();
		}
		childScriptContexts.add(context);
	}

	@Override
	public void setClassListener(ClassListener cl) {
		this.classListener = cl;
	}

	@Override
	public ClassListener getClassListener() {
		if (classListener != null) {
			return classListener;
		}
		if (parentScriptContext != null) {
			return parentScriptContext.getClassListener();
		}
		return null;
	}

	@Override
	public void setCompilerClassName(String className) {
		this.compilerClassName = className;
	}

	@Override
	public String getCompilerClassName() {
		return compilerClassName;
	}

	@Override
	public boolean equals(Object obj) {
		return obj instanceof ScriptContextImpl another && Arrays.equals(another.directories, directories);
	}

	@Override
	public int hashCode() {
		return Arrays.hashCode(directories);
	}
}
