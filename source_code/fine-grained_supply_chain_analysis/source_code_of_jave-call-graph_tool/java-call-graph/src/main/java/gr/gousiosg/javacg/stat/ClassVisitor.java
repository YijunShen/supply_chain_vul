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

import org.apache.bcel.classfile.Constant;
import org.apache.bcel.classfile.ConstantPool;
import org.apache.bcel.classfile.EmptyVisitor;
import org.apache.bcel.classfile.JavaClass;
import org.apache.bcel.classfile.Method;
import org.apache.bcel.generic.ConstantPoolGen;
import org.apache.bcel.generic.MethodGen;
import org.apache.bcel.generic.Type;

import java.util.ArrayList;
import java.util.List;
import java.io.*;
import java.io.File;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.regex.*;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import com.alibaba.fastjson.*;
import com.alibaba.fastjson.serializer.SerializerFeature;

public class ClassVisitor extends EmptyVisitor {

    private JavaClass clazz;
    private ConstantPoolGen constants;
    private String classReferenceFormat;
    private final DynamicCallManager DCManager = new DynamicCallManager();
    private List<String> methodCalls = new ArrayList<>();

    private String dir;
    private String fileName;
    private JSONObject object;
    
    private String cgroot, txtroot, jsonroot;

    public ClassVisitor(JavaClass jc, String filestr, String _cgroot) {
        clazz = jc; 
        constants = new ConstantPoolGen(clazz.getConstantPool());
        classReferenceFormat = "C:" + clazz.getClassName() + " %s";

        cgroot = _cgroot;
        txtroot = cgroot + "cgtxt/"; 
        jsonroot = cgroot + "classjson/"; 

        File file = new File(filestr);
        String name = file.getName();

        Pattern p = Pattern.compile("(.*)\\.jar$");
        Matcher m = p.matcher(name);

        dir = null;
        if(m.matches()){
            dir = jsonroot + m.group(1);
        }

        fileName = txtroot +  name  + "-single.txt"; 
        object = new JSONObject();
    }

    public void visitJavaClass(JavaClass jc) {
        jc.getConstantPool().accept(this);
        Method[] methods = jc.getMethods();

        String curClassName = jc.getClassName();
        String superClassName = jc.getSuperclassName();
        object.put("className", curClassName);

        object.put("superClassName", superClassName);
        object.put("isAbstract", jc.isAbstract());
        object.put("isFinal", jc.isFinal());
        object.put("isPublic", jc.isPublic());
        object.put("isProtected", jc.isProtected());
        object.put("isPrivate", jc.isPrivate()); 
        object.put("isInterface", jc.isInterface());

        String[] interNames = jc.getInterfaceNames();
        JSONObject interfaceObj = new JSONObject();
        for(int i = 0; i < interNames.length; ++i){
            interfaceObj.put(interNames[i], "true");
        }
        object.put("interNames", interfaceObj);

        JSONObject methodObj = new JSONObject();
        for (int i = 0; i < methods.length; i++) {
            Method method = methods[i];
            DCManager.retrieveCalls(method, jc);
            DCManager.linkCalls(method);
            method.accept(this); 

            MethodGen mg = new MethodGen(method, clazz.getClassName(), constants);
            String curMethodName = method.getName();
            String curMethodSigniture = method.getSignature();
            String argList = "(" + argumentList(mg.getArgumentTypes()) + ")";
            String rtType = method.getReturnType().toString();
            JSONObject methodDetailObj = new JSONObject();
            methodDetailObj.put("name", curMethodName);
            methodDetailObj.put("sig", curMethodSigniture);
            methodDetailObj.put("args", argList);
            methodDetailObj.put("rtType", rtType);
            methodDetailObj.put("isAbstract", method.isAbstract());
            methodDetailObj.put("isStatic", method.isStatic());
            methodDetailObj.put("isPrivate", method.isPrivate());
            methodDetailObj.put("isProtected", method.isProtected());
            methodDetailObj.put("isPublic", method.isPublic());
            methodDetailObj.put("isFinal", method.isFinal());
            methodDetailObj.put("type", "define");

            methodObj.put(curMethodName+argList, methodDetailObj);
        }
        object.put("methods", methodObj);
        object.put("finishedSearch", false);

        if(dir != null){
            String filePath = dir + "-json" + "/" + curClassName + ".json";
            createJsonFile(object, filePath);
        }
    }

    private String argumentList(Type[] arguments) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < arguments.length; i++) {
            if (i != 0) {
                sb.append(",");
            }
            sb.append(arguments[i].toString());
        }
        return sb.toString();
    }

    public void visitConstantPool(ConstantPool constantPool) {
        try{
            FileOutputStream fos = new FileOutputStream(fileName,true);

            for (int i = 0; i < constantPool.getLength(); i++) {
                Constant constant = constantPool.getConstant(i);
                if (constant == null)
                    continue;
                if (constant.getTag() == 7) {
                    String referencedClass = 
                        constantPool.constantToString(constant);
                    String s = String.format(classReferenceFormat, referencedClass) + '\n';
                    fos.write(s.getBytes()); 
                }
            }
            fos.close();
        }catch (IOException e) {
            e.printStackTrace(); 
        }
    }

    public void visitMethod(Method method) {
        MethodGen mg = new MethodGen(method, clazz.getClassName(), constants);
        MethodVisitor visitor = new MethodVisitor(mg, clazz);
        methodCalls.addAll(visitor.start());
    }

    public ClassVisitor start() {
        visitJavaClass(clazz);
        return this;
    }

    public List<String> methodCalls() {
        return this.methodCalls;
    }

    public static boolean createJsonFile(Object jsonData, String filePath) {
        String content = JSON.toJSONString(jsonData, SerializerFeature.PrettyFormat, SerializerFeature.WriteMapNullValue,
                SerializerFeature.WriteDateUseDateFormat);
        try {
            File file = new File(filePath);

            if (!file.getParentFile().exists()) {
                file.getParentFile().mkdirs();
            }

            if (file.exists()) {
                file.delete();
            }

            file.createNewFile();

            Writer write = new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8);
            write.write(content);
            write.flush();
            write.close();
            return true;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }
}