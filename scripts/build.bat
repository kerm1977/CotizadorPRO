@echo off
setlocal
cd /d "%~dp0.."
call scripts\setenv.bat
if %errorlevel% neq 0 exit /b 1
echo [BUILD] Sellando compilacion (buildstamp.js)...
node -e "require('fs').writeFileSync('www/js/buildstamp.js','// Regenerado por scripts\\build.bat en cada compilacion\r\nwindow.TRIBAL_BUILD = '+JSON.stringify(new Date().toLocaleString('sv-SE',{timeZone:'America/Costa_Rica'})+' CR')+';\r\n')"
echo [BUILD] Sincronizando Capacitor...
call npx cap sync android
if %errorlevel% neq 0 exit /b 1
cd android
echo [BUILD] Compilando APK...
call gradlew.bat assembleDebug -Dorg.gradle.java.home="%JAVA_HOME%" --no-daemon
if %errorlevel% equ 0 (
  if not exist ..\apks mkdir ..\apks
  move /y app\build\outputs\apk\debug\app-debug.apk ..\apks\app-debug.apk >nul
  echo [BUILD] APK listo: apks\app-debug.apk
)
