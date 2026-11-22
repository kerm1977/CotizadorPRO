package com.miapp.local;

import android.app.Activity;
import android.Manifest;
import android.content.Intent;
import android.net.Uri;
import androidx.activity.result.ActivityResult;
import androidx.core.content.FileProvider;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

/** PickImage — selector de imagen nativo.
 *  pick({camera:false}) → galería SAF (ACTION_OPEN_DOCUMENT)
 *  pick({camera:true})  → cámara (ACTION_IMAGE_CAPTURE + FileProvider);
 *    pide el permiso CAMERA en el momento si falta.
 *  Ambos copian el resultado a cache/pick_*.jpg y resuelven {path};
 *  JS lo muestra con Capacitor.convertFileSrc(path). {cancelled:true}
 *  si el usuario cierra el picker sin elegir. */
@CapacitorPlugin(name = "PickImage", permissions = {
    @Permission(alias = "camera", strings = { Manifest.permission.CAMERA })
})
public class PickImagePlugin extends Plugin {

    private File pendingCam;

    @PluginMethod
    public void pick(PluginCall call) {
        try {
            boolean cam = Boolean.TRUE.equals(call.getBoolean("camera", false));
            if (cam && getPermissionState("camera") != PermissionState.GRANTED) {
                requestPermissionForAlias("camera", call, "cameraPerm");
                return;
            }
            launch(call, cam);
        } catch (Exception e) {
            call.reject("pick: " + e.getMessage());
        }
    }

    @PermissionCallback
    private void cameraPerm(PluginCall call) {
        if (getPermissionState("camera") == PermissionState.GRANTED) {
            launch(call, true);
        } else {
            call.reject("permiso de cámara denegado — activalo en Ajustes → Aplicaciones → CotizacionesPro → Permisos");
        }
    }

    private void launch(PluginCall call, boolean cam) {
        try {
            if (cam) launchCamera(call); else launchGallery(call);
        } catch (Exception e) {
            call.reject("pick: " + e.getMessage());
        }
    }

    private void launchGallery(PluginCall call) {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.setType("image/*");
        i.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(call, i, "galleryDone");
    }

    private void launchCamera(PluginCall call) throws Exception {
        pendingCam = new File(getContext().getCacheDir(),
            "pick_cam_" + System.currentTimeMillis() + ".jpg");
        Uri out = FileProvider.getUriForFile(getContext(),
            getContext().getPackageName() + ".fileprovider", pendingCam);
        Intent i = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
        i.putExtra(android.provider.MediaStore.EXTRA_OUTPUT, out);
        i.putExtra("android.intent.extras.CAMERA_FACING",
            android.hardware.camera2.CameraMetadata.LENS_FACING_FRONT);
        i.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                 | Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivityForResult(call, i, "cameraDone");
    }

    @ActivityCallback
    private void galleryDone(PluginCall call, ActivityResult result) {
        JSObject ret = new JSObject();
        try {
            if (result.getResultCode() == Activity.RESULT_OK
                    && result.getData() != null) {
                Uri uri = result.getData().getData();
                InputStream in = getContext().getContentResolver()
                    .openInputStream(uri);
                if (in == null) { ret.put("cancelled", true); }
                else {
                    String mime = getContext().getContentResolver().getType(uri);
                    String ext = extOf(mime);
                    // un solo archivo vigente: pick_current.<ext> sustituye al anterior
                    File f = new File(getContext().getCacheDir(),
                        "pick_current." + ext);
                    copyTo(in, f);
                    cleanPicks(f);
                    ret.put("path", f.getAbsolutePath());
                }
            } else ret.put("cancelled", true);
        } catch (Exception e) { ret.put("error", e.getMessage()); }
        call.resolve(ret);
    }

    @ActivityCallback
    private void cameraDone(PluginCall call, ActivityResult result) {
        JSObject ret = new JSObject();
        try {
            if (result.getResultCode() == Activity.RESULT_OK && pendingCam != null
                    && pendingCam.isFile() && pendingCam.length() > 0) {
                File f = new File(getContext().getCacheDir(),
                    "pick_current.jpg");
                java.io.FileInputStream in = new java.io.FileInputStream(pendingCam);
                copyTo(in, f);
                cleanPicks(f);
                ret.put("path", f.getAbsolutePath());
            } else ret.put("cancelled", true);
        } catch (Exception e) { ret.put("error", e.getMessage()); }
        if (pendingCam != null) pendingCam.delete();
        pendingCam = null;
        call.resolve(ret);
    }

    private String extOf(String mime) {
        if (mime == null) return "img";
        if (mime.contains("png")) return "png";
        if (mime.contains("webp")) return "webp";
        if (mime.contains("gif")) return "gif";
        return "jpg";
    }

    // borra todos los temporales pick_* menos el archivo vigente
    private void cleanPicks(File keep) {
        File[] fs = getContext().getCacheDir().listFiles(
            (d, n) -> n.startsWith("pick_") && !n.equals(keep.getName()));
        if (fs != null) for (File f : fs) f.delete();
    }

    private void copyTo(InputStream in, File f) throws Exception {
        FileOutputStream fos = new FileOutputStream(f);
        byte[] buf = new byte[65536]; int r;
        while ((r = in.read(buf)) != -1) fos.write(buf, 0, r);
        fos.close(); in.close();
    }
}
