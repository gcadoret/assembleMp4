#!/usr/bin/env python3
import argparse
import subprocess
import sys
import shlex
from pathlib import Path
import re
import tempfile

def natural_key(s: str):
    """Retourne une clé de tri alpha-numérique (ex: 51.9 < 51.29 < 52.09)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def build_list_file(files):
    import tempfile
    from pathlib import Path
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    for f in files:
        p = Path(f).resolve() 
        tmp.write(f"file '{p.as_posix()}'\n")
    tmp.flush()
    tmp.close()
    return tmp.name

def run(cmd):
    print(f"\n$ {cmd}\n", flush=True)
    proc = subprocess.run(cmd, shell=True)
    return proc.returncode

def main():
    parser = argparse.ArgumentParser(description="Assembler des MP4 dans l'ordre alpha-numérique.")
    parser.add_argument("--input-dir", "-i", type=Path, default=Path("."), help="Dossier contenant les .mp4")
    parser.add_argument("--output", "-o", type=Path, default=Path("video_assemblee.mp4"), help="Fichier de sortie")
    parser.add_argument("--pattern", "-p", type=str, default="*.mp4", help="Motif de fichiers (glob)")
    parser.add_argument("--reencode", action="store_true", help="Forcer le ré-encodage (H.264 + AAC)")
    args = parser.parse_args()

    if not args.input_dir.exists():
        print(f"Dossier introuvable: {args.input_dir}", file=sys.stderr)
        sys.exit(2)

    files = sorted([str(p) for p in args.input_dir.glob(args.pattern)], key=natural_key)
    if not files:
        print("Aucun fichier .mp4 trouvé.", file=sys.stderr)
        sys.exit(3)

    print("Ordre d'assemblage :")
    for f in files:
        print(" -", Path(f).name)

    list_path = build_list_file(files)

    if not args.reencode:
        # Concat rapide : pas de ré-encodage (nécessite mêmes codecs/params)
        cmd_copy = (
            f"ffmpeg -hide_banner -loglevel warning -y -f concat -safe 0 -i {shlex.quote(list_path)} "
            f"-c copy -movflags +faststart {shlex.quote(str(args.output))}"
        )
        rc = run(cmd_copy)
        if rc == 0:
            print(f"\n✅ Terminé (copie sans ré-encodage) → {args.output}")
            sys.exit(0)
        else:
            print("\n⚠️  Concat sans ré-encodage a échoué. Tentative avec ré-encodage...")

    # Fallback / ré-encodage forcé : uniformise en H.264 + AAC
    cmd_reencode = (
        f"ffmpeg -hide_banner -loglevel warning -y -f concat -safe 0 -i {shlex.quote(list_path)} "
        f"-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "
        f"-c:a aac -b:a 192k -movflags +faststart {shlex.quote(str(args.output))}"
    )
    rc2 = run(cmd_reencode)
    if rc2 != 0:
        print("\n❌ Échec de l'assemblage même avec ré-encodage.", file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ Terminé (ré-encodage) → {args.output}")

if __name__ == "__main__":
    main()