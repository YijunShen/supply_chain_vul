/*
 * Copyright (c) 2011 - Georgios Gousios <gousiosg@gmail.com>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *
 *     * Redistributions in binary form must reproduce the above
 *       copyright notice, this list of conditions and the following
 *       disclaimer in the documentation and/or other materials provided
 *       with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package gr.gousiosg.javacg.stat;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.util.function.Function; 
import java.util.jar.JarEntry;
import java.util.jar.JarFile; 
import java.util.jar.Manifest;
import java.util.stream.Stream; 
import java.util.stream.StreamSupport;

import org.apache.bcel.classfile.ClassParser;

/**
 * Constructs a callgraph out of a JAR archive. Can combine multiple archives
 * into a single call graph.
 * @author Georgios Gousios <gousiosg@gmail.com>
 */
public class JCallGraph {

    public static void main(String[] args) {

     String [] test = {"/home/sdp/science/lcp/CallGraph/data/test/org.javamoney.moneta--moneta-core--1.3.jar", "/home/sdp/science/lcp/CallGraph/data/test/rlt/"};
                    
        args = test;

        final String filestr = args[0];

        final String cgroot = args[1];

        final String txtroot = cgroot + "cgtxt/";
        final String jsonroot = cgroot + "classjson/";
        File txtfile = new File(txtroot);
        File jsonfile = new File(jsonroot);
        boolean txtrlt = txtfile.mkdirs();
        boolean jsonrlt = jsonfile.mkdirs();
        
        File file = new File(filestr); 
        String name = file.getName(); 
        String path = file.getParent();

        String depjson = path + "/deps.json";
       
        final String fileName = txtroot +  name  + "-single.txt"; 

        Function<ClassParser, ClassVisitor> getClassVisitor =
                (ClassParser cp) -> {
                    try {
                        return new ClassVisitor(cp.parse(), filestr, cgroot); 
                    } catch (IOException e) {
                        throw new UncheckedIOException(e);
                    }
                };

        try {
            FileOutputStream fileOutputStream = new FileOutputStream(fileName);
            fileOutputStream.getChannel().truncate(0);
            fileOutputStream.close();

            String arg = args[0];
            File f = new File(arg);

            if (!f.exists()) {
                System.err.println("Jar file " + arg + " does not exist");
            }

            try (JarFile jar = new JarFile(f)) {
                Set<String> diffClassPaths  = Clean.diffALLDeps(filestr, depjson);

                Stream<JarEntry> entries = jar.stream().
                                filter(jarEntry -> diffClassPaths.contains(jarEntry.getName()));

                String methodCalls = entries.
                        flatMap(e -> {
                            if (e.isDirectory() || !e.getName().endsWith(".class"))
                                return (new ArrayList<String>()).stream();
                            ClassParser cp = new ClassParser(arg, e.getName()); 

                            return getClassVisitor.apply(cp).start().methodCalls().stream();
                        }).
                        map(s -> s + "\n").
                        reduce(new StringBuilder(),
                                StringBuilder::append,
                                StringBuilder::append).toString();

                OutputStreamWriter oStreamWriter = new OutputStreamWriter(new FileOutputStream(fileName, true), "utf-8");
                oStreamWriter.append(methodCalls);
                oStreamWriter.close();

            }
        } catch (IOException e) {
            System.err.println("Error while processing jar: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static <T> Stream<T> enumerationAsStream(Enumeration<T> e) {
        return StreamSupport.stream(
                Spliterators.spliteratorUnknownSize(
                        new Iterator<T>() {
                            public T next() {
                                return e.nextElement();
                            }

                            public boolean hasNext() {
                                return e.hasMoreElements();
                            }
                        },
                        Spliterator.ORDERED), false);
    }

    public static boolean isMavenJar(String jarFilePath)  {
        try (JarFile jarFile = new JarFile(jarFilePath)) {
            if (jarFile.getEntry("META-INF") == null) {
                System.out.println(jarFilePath + " does not contain META-INF/ !");
                return false;
            }

            Manifest manifest = jarFile.getManifest();
            String manifestVersion = manifest.getMainAttributes().getValue("Manifest-Version");
            if (manifestVersion == null || !manifestVersion.matches("\\d+\\.\\d+")) {
                System.out.println(jarFilePath + ": MANIFEST.MF does not contain Manifest-Version !");
                return false;
            }

            if (jarFile.getEntry("META-INF/maven") == null) {
                System.out.println(jarFilePath + " does not contain META-INF/maven !");
                return false;
            }
            
            for (JarEntry entry : Collections.list(jarFile.entries())) {
                if (!entry.isDirectory() && entry.getName().endsWith(".class") && !isValidClassName(entry.getName())) {
                    System.out.println("error class name: " + entry.getName());
                    return false;
                }
            }
            
            return true;
        } catch (IOException e) {
            System.err.println("Error reading jar file: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    private static boolean isValidClassName(String className) {
        String[] parts = className.split("/");
        String simpleName = parts[parts.length - 1].replace(".class", "");
        String packageName = String.join(".", Arrays.asList(parts).subList(0, parts.length - 1));
    
        String expectedClassName = packageName.isEmpty() ? simpleName : packageName + "." + simpleName;
        if (!expectedClassName.equals(simpleName)){
            System.out.println("expectedClassName: " + expectedClassName);
            System.out.println("actualClassName: " + simpleName);
            return false;
        }
        return true;
    }
}