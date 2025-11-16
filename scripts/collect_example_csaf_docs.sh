#!/bin/bash

set -e

dirname=csafs
loads_dirname=$dirname/loads
some_dirname=$dirname/some

cd "$(git rev-parse --show-toplevel)"
mkdir -p $dirname
mkdir -p $loads_dirname

./scripts/ensure_csaf_tools.sh

number_of_files=$(find "$loads_dirname" -type f -name "*.json" | wc -l)
echo "Currently storing $number_of_files CSAF documents in $loads_dirname."
if [ $number_of_files -lt 10 ]; then
    echo "Downloading CSAF documents to $loads_dirname."
    echo "NOTE: This will take some time on the order of 15 minutes."
    ./csaf_downloader -d $loads_dirname https://cert-bund.de/.well-known/csaf/provider-metadata.json
fi

echo "Copying some CSAF documents to $some_dirname."
rm -rf $some_dirname
mkdir $some_dirname

year_dirs=$(ls "$loads_dirname/white/" | grep -E '^[0-9]{4}$' | awk '$1 > 2020')
for year in $year_dirs; do
    mkdir -p $some_dirname/white
    target_dir=$some_dirname/white/$year
    mkdir -p $target_dir
    files=("$loads_dirname/white/$year"/*)
    for i in 0 1 2 3; do # Only copy the first four files (json, signature, sha256, sha512) of each year
        [ -e "${files[$i]}" ] && cp "${files[$i]}" "$target_dir/"
    done
done

if ! command -v jq &> /dev/null; then
    sudo aptitude install -y jq
fi

function fake_docs() {
    Tlp="$1"
    TLP=$(echo "$Tlp" | tr '[:lower:]' '[:upper:]')
    tlp=$(echo "$Tlp" | tr '[:upper:]' '[:lower:]')

    white_csafs=$(find $some_dirname/white -type f -name "*.json")
    year_dirs=$(ls "$some_dirname/white/")
    echo "Faking some $TLP CSAF documents"
    mkdir -p "$some_dirname/$tlp"
    for year in $year_dirs; do
        mkdir -p $some_dirname/$tlp/$year
    done
    for file in $white_csafs; do
        new_path=$(echo $file | sed "s/white/$tlp/" | sed "s/.json/-$tlp.json/")
        if [ "$tlp" == "unlabeled" ]; then
            jq 'del(.document.distribution) | .document.tracking.id += "-unlabeled"' "$file" > "$new_path"
        else
            jq ".document.distribution.tlp.label = \"$TLP\" | .document.tracking.id += \"-$tlp\"" "$file" > "$new_path"
        fi
        # These hashes and signatures are now wrong, of course.
        cp $file.asc "$new_path.asc"
        cp $file.sha256 "$new_path.sha256"
        cp $file.sha512 "$new_path.sha512"
    done
}

fake_docs "CLEAR"
fake_docs "GREEN"
fake_docs "AMBER"
fake_docs "AMBER+STRICT"
fake_docs "RED"
fake_docs "unlabeled"
