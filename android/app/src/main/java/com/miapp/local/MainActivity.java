package com.miapp.local;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.res.Configuration;
import android.util.DisplayMetrics;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.View;
import android.view.Window;
import android.webkit.MimeTypeMap;
import android.webkit.PermissionRequest;
import com.getcapacitor.BridgeWebChromeClient;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;

import com.getcapacitor.BridgeActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

// Recibe "Abrir con" (VIEW) y "Compartir" (SEND / SEND_MULTIPLE):
// copia el stream entrante a files/tribu_inbox/ y avisa al WebView con el
// evento 'tribalInbox'. El módulo js/media/inbox.js importa lo recibido.
public class MainActivity extends BridgeActivity {

    // La escala de fuente y de pantalla del sistema (letra/íconos más
    // grandes en Ajustes) no debe descuadrar la interfaz: se fija la
    // configuración al tamaño estándar para toda la app.
    @Override
    protected void attachBaseContext(Context newBase) {
        try {
            Configuration cfg = new Configuration(
                newBase.getResources().getConfiguration());
            cfg.fontScale = 1.0f;
            cfg.densityDpi = DisplayMetrics.DENSITY_DEVICE_STABLE;
            super.attachBaseContext(
                newBase.createConfigurationContext(cfg));
        } catch (Throwable ignored) {
            super.attachBaseContext(newBase);
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(TribalFtpPlugin.class);
        registerPlugin(PickImagePlugin.class);
        super.onCreate(savedInstanceState);
        setupSystemBarsSafeArea();
        requestAllPermissions();
        lockWebViewTextZoom();
    }

    @Override
    public void onResume() {
        super.onResume();
        lockWebViewTextZoom();
    }

    // Zoom de texto del WebView clavado en 100%: la fuente del sistema no
    // agranda el texto dentro de las páginas de la app.
    private void lockWebViewTextZoom() {
        try {
            android.webkit.WebView wv =
                getBridge() != null ? getBridge().getWebView() : null;
            if (wv != null) wv.getSettings().setTextZoom(100);
        } catch (Throwable ignored) {}
    }

    // Garantiza que el WebView respete la barra superior de estado y la barra
    // inferior de navegación de Samsung/Android sin superponerse jamás.
    private void setupSystemBarsSafeArea() {
        try {
            Window w = getWindow();
            if (w == null) return;
            WindowCompat.setDecorFitsSystemWindows(w, true);
            w.setStatusBarColor(0xFFE9E2F7);
            w.setNavigationBarColor(0xFFE9E2F7);
            final View content = w.findViewById(android.R.id.content);
            if (content != null) {
                content.setBackgroundColor(0xFFE9E2F7);
                ViewCompat.setOnApplyWindowInsetsListener(content, (v, windowInsets) -> {
                    Insets bars = windowInsets.getInsets(
                        WindowInsetsCompat.Type.systemBars()
                        | WindowInsetsCompat.Type.displayCutout()
                        | WindowInsetsCompat.Type.ime()
                    );
                    v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                    return WindowInsetsCompat.CONSUMED;
                });
            }
        } catch (Throwable ignored) {}
    }

    // Pide TODOS los permisos runtime de una vez al arrancar. Android solo
    // muestra diálogo por los que falten; los ya concedidos se omiten solos.
    // Si el usuario revocó algo, se le vuelve a pedir en el próximo arranque —
    // así el permiso no puede quedar "apagado" en silencio.
    private void requestAllPermissions() {
        List<String> want = new ArrayList<>();
        // fotos: cámara siempre; galería según versión de Android
        want.add(Manifest.permission.CAMERA);
        if (Build.VERSION.SDK_INT >= 33)
            want.add(Manifest.permission.READ_MEDIA_IMAGES);
        else
            want.add(Manifest.permission.READ_EXTERNAL_STORAGE);
        List<String> missing = new ArrayList<>();
        List<String> nowGranted = new ArrayList<>();
        for (String p : want) {
            if (checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED)
                nowGranted.add(p);
            else missing.add(p);
        }
        // pedir UNA vez: el set everGranted recuerda lo que se concedió.
        // Solo se vuelve a pedir si falta algo que ANTES estaba concedido
        // (el usuario lo revocó) — lo negado de entrada nunca se insiste;
        // para eso queda el botón "Solicitar permisos" en el menú.
        SharedPreferences sp =
            getSharedPreferences("tribu_perms", MODE_PRIVATE);
        java.util.Set<String> ever = new java.util.HashSet<>(
            sp.getStringSet("everGranted", new java.util.HashSet<String>()));
        boolean firstRun = !sp.contains("everGranted");
        List<String> toAsk = new ArrayList<>();
        if (firstRun) {
            toAsk.addAll(missing);
        } else {
            for (String p : missing)
                if (ever.contains(p)) toAsk.add(p);   // revocado → repedir
        }
        if (!toAsk.isEmpty()) {
            try {
                requestPermissions(toAsk.toArray(new String[0]), 7712);
            } catch (Exception ignored) {}
        }
        ever.addAll(nowGranted);
        sp.edit().putStringSet("everGranted", ever).apply();
    }

    // lo concedido en el diálogo entra al set al instante (sin esperar
    // al próximo arranque) — así detectar revocación es exacto
    @Override
    public void onRequestPermissionsResult(int rc, String[] perms,
                                           int[] results) {
        super.onRequestPermissionsResult(rc, perms, results);
        if (rc != 7712) return;
        SharedPreferences sp = getSharedPreferences("tribu_perms", MODE_PRIVATE);
        java.util.Set<String> ever = new java.util.HashSet<>(
            sp.getStringSet("everGranted", new java.util.HashSet<String>()));
        for (int i = 0; i < perms.length; i++)
            if (results[i] == PackageManager.PERMISSION_GRANTED)
                ever.add(perms[i]);
        sp.edit().putStringSet("everGranted", ever).apply();
    }

}
