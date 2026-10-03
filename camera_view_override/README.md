# Legacy SurfaceView preview control

[src] CameraX 1.5.0 PreviewView selects TextureView for LEGACY camera backends.
The M8 framework shim draws complete GL buffers into consumer surfaces; the
opt-in control lets a verified backend use SurfaceView in PERFORMANCE mode.
API levels through 24, existing SurfaceView device quirks, and COMPATIBLE
mode retain their upstream selection. The caller must verify geometry,
rotation, metering, overlays and surface lifecycle before enabling the option.

[src] PreviewView.java comes from Google's camera-view 1.5.0 source archive:
https://dl.google.com/dl/android/maven2/androidx/camera/camera-view/1.5.0/camera-view-1.5.0-sources.jar
(SHA256 3ca2e5448b7b281982b0d99ec27e6fd6cafb3b9eba71d68a5f215e4607644297).
The original PreviewView class group matches the published AAR byte for byte.
The vendored AAR retains separate CameraController and ZoomGestureDetector
changes and has SHA256
da2092eca64f5539b373fb4bda1955ce749c0367a1d8766dca7a474706011810.
Use that vendored archive as the retained base, rather than Google's AAR.

[src] rebuild.py compiles the PreviewView class group with Java 17,
-Xlint:all and -Werror, uses fixed ZIP timestamps for replacement classes,
and verifies identical bytes for every retained class and AAR member.
Provide the app's generated dependency JAR paths one per line in a
classpath file and retain the base AAR separately. Invoke the script through
$PYTHON with --base-aar, --classpath-file, --javac, --work-directory and
--output. The work directory must be fresh. Running the same inputs twice
must produce the same output SHA256. The ordinary Aperture target compiles
and dexes the resulting vendored AAR.

[src] Aperture gates the hidden legacy_surface_preview preference to API-35
m8/m8whl and defaults it to false. Configure the preference before activity
creation. [inf] Device admission remains required: the control must preserve
preview rate and geometry, tap-to-focus, crop, overlays and lifecycle while
meeting loaded recording acceptance. Workbench PR 189 retains measurements.
