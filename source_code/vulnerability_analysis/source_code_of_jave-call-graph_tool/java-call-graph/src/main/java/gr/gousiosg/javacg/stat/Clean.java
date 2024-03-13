package gr.gousiosg.javacg.stat;

import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.io.*;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

import com.alibaba.fastjson.*;

public class Clean {
    final static String jarroot = "/home/sdp/science/lcp/CallGraph/data/jars/";

    public static void diff(String jp1, String jp2){
        try{
            File jar1File = new File(jp1);
            File jar2File = new File(jp2);
            JarFile jar1 = new JarFile(jar1File);
            JarFile jar2 = new JarFile(jar2File);

            Set<String> jar1ClassPaths = jar1.stream()
                    .filter(jarEntry -> jarEntry.getName().endsWith(".class"))
                    .map(JarEntry::getName)
                    .collect(Collectors.toSet());

            Set<String> jar2ClassPaths = jar2.stream()
                    .filter(jarEntry -> jarEntry.getName().endsWith(".class"))
                    .map(JarEntry::getName)
                    .collect(Collectors.toSet());

            Set<String> diffClassPaths = new HashSet<>(jar1ClassPaths);
            diffClassPaths.removeAll(jar2ClassPaths);

            Stream<JarEntry> diffJarEntries = jar1.stream()
                    .filter(jarEntry -> diffClassPaths.contains(jarEntry.getName()));

            System.out.println("rlt type: " + (diffJarEntries.getClass()));

            System.out.println("class paths1: "+(jar1ClassPaths.size()));
            System.out.println("class paths2: "+(jar2ClassPaths.size()));
            System.out.println("class paths in paths1 not path2: "+(diffClassPaths.size()));

            jar1.close();
            jar2.close();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public static Set<String> getClassPaths(File jarFile) throws IOException{
        JarFile jar = new JarFile(jarFile);

        Set<String> jarClassPaths = jar.stream()
                .filter(jarEntry -> jarEntry.getName().endsWith(".class"))
                .map(JarEntry::getName)
                .collect(Collectors.toSet());
            
        jar.close();
        return jarClassPaths;
	}

    public static Set<String> diffALL(String jp1, String deppath){
        try{
            File jarFile1 = new File(jp1);
            Set<String> jar1ClassPaths = getClassPaths(jarFile1);

            Set<String> diffClassPaths = new HashSet<>(jar1ClassPaths);

            File file = new File(deppath);   

            File[] array = file.listFiles();   

            for(int i = 0; i < array.length; ++i){
                if(array[i].isFile()){
                    Set<String> curDepClassPaths = getClassPaths(array[i]);
                    diffClassPaths.removeAll(curDepClassPaths); 
                }
            }
            return diffClassPaths;
            
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    } 

    public static Set<String> diffALLDeps(String jp1, String depJsonPath){
        try{
            File jarFile1 = new File(jp1);
            Set<String> jar1ClassPaths = getClassPaths(jarFile1);

            Set<String> diffClassPaths = new HashSet<>(jar1ClassPaths);

            File depjsonFile = new File(depJsonPath);

            if (depjsonFile.exists()){
                String jsonString = new String(Files.readAllBytes(Paths.get(depJsonPath)), StandardCharsets.UTF_8);
                JSONArray jsonArray = JSON.parseArray(jsonString);

                for (Object obj : jsonArray) {
                    JSONObject jsonObj = (JSONObject) obj;
                    String depGroup = jsonObj.getString("groupId");
                    String depArtifact = jsonObj.getString("artifactId");
                    String depVersion = jsonObj.getString("version");

                    String depJarName = depGroup + "--" + depArtifact + "--" + depVersion + ".jar";
                    String depgroupPath = depGroup.replace(".", "/");
                    String depJarPath = jarroot + depgroupPath + "/" + depArtifact + "/" + depVersion + "/" + depJarName;

                    File depJarFile = new File(depJarPath);
                    if (depJarFile.exists()) {
                        Set<String> curDepClassPaths = getClassPaths(depJarFile);
                        diffClassPaths.removeAll(curDepClassPaths); 
                    }
                }
            }

            return diffClassPaths;
            
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        } 
    } 


    public static void readJson(String jsonPath){
        try{
            String jsonString = new String(Files.readAllBytes(Paths.get(jsonPath)), StandardCharsets.UTF_8);
            JSONArray jsonArray = JSON.parseArray(jsonString);

            System.out.println("total: "+jsonArray.size());
            for (Object obj : jsonArray) {
                JSONObject jsonObj = (JSONObject) obj;
                System.out.println(jsonObj.getString("groupId") + ":" + jsonObj.getString("artifactId") + ":" + jsonObj.getString("version"));
            }

        } catch (IOException e) {
            System.err.println("Error while read json " + jsonPath + " : "+ e.getMessage());
            e.printStackTrace();
        }
    }
}