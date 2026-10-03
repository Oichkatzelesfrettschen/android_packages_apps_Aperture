"""Rebuild the PreviewView class group in the pinned vendored CameraX AAR."""

import argparse
import copy
import hashlib
import io
from pathlib import Path
import subprocess
import zipfile

BASE_SHA256 = "da2092eca64f5539b373fb4bda1955ce749c0367a1d8766dca7a474706011810"
CLASS_PREFIX = "androidx/camera/view/PreviewView"


def preview_class(name: str) -> bool:
    return name == CLASS_PREFIX + ".class" or name.startswith(CLASS_PREFIX + "$")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-aar", type=Path, required=True)
    parser.add_argument("--classpath-file", type=Path, required=True)
    parser.add_argument("--javac", type=Path, required=True)
    parser.add_argument("--work-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    original_bytes = arguments.base_aar.read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != BASE_SHA256:
        raise ValueError("base AAR differs from the pinned vendored CameraX archive")
    if arguments.base_aar.resolve() == arguments.output.resolve():
        raise ValueError("output must differ from the retained base archive")
    classes = arguments.work_directory / "classes"
    classes.mkdir(parents=True, exist_ok=False)
    source = (
        Path(__file__).resolve().parent / "src/androidx/camera/view/PreviewView.java"
    )
    classpath = arguments.classpath_file.read_text().splitlines()
    if not classpath or any(not Path(member).is_file() for member in classpath):
        raise ValueError("classpath must list existing JAR files, one per line")
    subprocess.run(
        [
            str(arguments.javac),
            "--release",
            "17",
            "-proc:none",
            "-Xlint:all",
            "-Werror",
            "-classpath",
            ":".join(classpath),
            "-d",
            str(classes),
            str(source),
        ],
        check=True,
    )
    replacement_names = []
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as original:
        jar_bytes = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original.read("classes.jar"))) as old_jar:
            with zipfile.ZipFile(
                jar_bytes, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
            ) as new_jar:
                for member in old_jar.infolist():
                    if not preview_class(member.filename):
                        new_jar.writestr(
                            copy.copy(member), old_jar.read(member.filename)
                        )
                for compiled in sorted(classes.rglob("*.class")):
                    name = compiled.relative_to(classes).as_posix()
                    if not preview_class(name):
                        raise ValueError("compiler emitted a class outside PreviewView")
                    member = zipfile.ZipInfo(name, (2008, 1, 1, 0, 0, 0))
                    member.compress_type = zipfile.ZIP_DEFLATED
                    new_jar.writestr(member, compiled.read_bytes())
                    replacement_names.append(name)
            with zipfile.ZipFile(io.BytesIO(jar_bytes.getvalue())) as new_jar:
                for name in old_jar.namelist():
                    if not preview_class(name) and old_jar.read(name) != new_jar.read(
                        name
                    ):
                        raise ValueError("a retained class member changed")
        if CLASS_PREFIX + ".class" not in replacement_names:
            raise ValueError("compiler emitted no PreviewView class")
        output_bytes = io.BytesIO()
        with zipfile.ZipFile(
            output_bytes, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as updated:
            for member in original.infolist():
                data = (
                    jar_bytes.getvalue()
                    if member.filename == "classes.jar"
                    else original.read(member.filename)
                )
                updated.writestr(copy.copy(member), data)
        with zipfile.ZipFile(io.BytesIO(output_bytes.getvalue())) as updated:
            if set(original.namelist()) != set(updated.namelist()):
                raise ValueError("AAR member set changed")
            for name in original.namelist():
                if name != "classes.jar" and original.read(name) != updated.read(name):
                    raise ValueError("a retained AAR member changed")
    arguments.output.write_bytes(output_bytes.getvalue())
    print(hashlib.sha256(output_bytes.getvalue()).hexdigest())


if __name__ == "__main__":
    main()
