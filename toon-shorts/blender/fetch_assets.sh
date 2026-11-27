#!/usr/bin/env bash
# Rebuilds toon-shorts/assets3d/ (git-ignored) from sources that allow automated downloads:
#  - Kenney's official MIT-licensed starter kits on GitHub (city buildings/roads, vehicles)
#  - a CC0 overcast sky HDRI from Poly Haven
# Kenney's full CC0 packs (kenney.nl) refuse automated downloads: download those in a browser
# and unzip them into assets3d/kenney/ by hand.
set -euo pipefail
cd "$(dirname "$0")/.."
A=assets3d; T=$(mktemp -d)
mkdir -p "$A/kenney/city/Textures" "$A/kenney/racing/Textures"
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/KenneyNL/starter-kit-city-builder "$T/city"
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/KenneyNL/starter-kit-racing "$T/racing"
cp "$T"/city/models/*.glb "$A/kenney/city/";   cp "$T/city/models/Textures/colormap.png" "$A/kenney/city/Textures/";   cp "$T/city/LICENSE.md" "$A/kenney/city/"
cp "$T"/racing/models/*.glb "$A/kenney/racing/"; cp "$T/racing/models/Textures/colormap.png" "$A/kenney/racing/Textures/"; cp "$T/racing/LICENSE" "$A/kenney/racing/"
curl -sSL -o "$A/sky_overcast.hdr" https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/kloofendal_overcast_puresky_2k.hdr
rm -rf "$T"
echo "assets ready in $A"
