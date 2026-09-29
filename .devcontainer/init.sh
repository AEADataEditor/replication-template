#!/bin/sh
 if [ ! -f stata.lic ]
 then
    if [ -z ${STATA_LIC_BASE64} ]
    then
        echo "No license found."
        exit 2
    else
        echo "${STATA_LIC_BASE64}" | base64 -d > stata.lic 
    fi
fi
#docker buildx install

# Install packages we may need
apt-get update && apt-get install -y \
   curl \
   pandoc \
   wkhtmltopdf

# AEA specific stuff
#git clone https://github.com/AEADataEditor/editor-scripts.git /home/codespace/.local/bin 
#UNZIP=$(tempfile)
wget https://github.com/AEADataEditor/editor-scripts/archive/refs/heads/main.zip -O /tmp/main.zip && unzip -d /home/codespace/.local/bin -j /tmp/main.zip

echo "init done."