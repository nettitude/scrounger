#! /bin/bash

function log(){
    echo "[+]" $1;
}

function error(){
    echo "[-] " $1;
}

function die(){
    error $1;
    exit 1;
}

# Guess SHELLrc file
SHELL_NAME=$(echo $SHELL | awk -F"/" '{print $NF}');
SHELL_RC=$HOME/.$SHELL_NAME"rc";

function install(){
    log "Installing Dependencies";

    ORIGINAL_PWD=$(pwd)

    # install jd-cli
    if [ ! -x "$(command -v jd-cli)" ]; then
        curl -L -o /tmp/jdcli.zip https://github.com/kwart/jd-cmd/releases/download/jd-cmd-0.9.2.Final/jd-cli-0.9.2-dist.zip
        unzip /tmp/jdcli.zip /usr/local/share/jd-cli
        ln -s /usr/local/share/jd-cli/jd-cli /usr/local/bin/jd-cli
        ln -s /usr/local/share/jd-cli/jd-cli.jar /usr/local/bin/jd-cli.jar
        rm -rf /tmp/jdcli.zip
    fi

    # install apktool
    if [ ! -x "$(command -v apktool)" ]; then
        mkdir /usr/local/share/apktool
        curl -L -o /usr/local/share/apktool/apktool https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/osx/apktool
        curl -L -o /usr/local/share/apktool/apktool.jar https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.3.3.jar
        chmod +x /usr/local/share/apktool /usr/local/share/apktool/apktool.jar
        ln -s /usr/local/share/apktool /usr/local/bin/apktool
        ln -s /usr/local/share/apktool.jar /usr/local/bin/apktool.jar
    fi

    # install dex2jar
    if [ ! -x "$(command -v d2j-dex2jar.sh)" ]; then
        curl -L -o /tmp/d2j.zip https://github.com/pxb1988/dex2jar/files/1867564/dex-tools-2.1-SNAPSHOT.zip
        unzip /tmp/d2j.zip -d /tmp/d2j
        dirname=$(ls --color=none /tmp/d2j)
        mv /tmp/d2j/$dirname /usr/local/share/d2j-dex2jar
        ln -s /usr/local/share/d2j-dex2jar/d2j-dex2jar.sh /usr/local/bin/d2j-dex2jar.sh
        ln -s /usr/local/share/d2j-dex2jar/d2j-apk-sign.sh /usr/local/bin/d2j-apk-sign.sh
        rm -rf /tmp/d2j.zip
    fi

    if [ ! -x "$(command -v d2j-dex2jar)" ]; then
        ln -s $(command -v d2j-dex2jar.sh) /usr/local/bin/d2j-dex2jar
    fi

    # install adb
    if [ ! -x "$(command -v adb)" ]; then
        curl -L -o /tmp/platform-tools.zip https://dl.google.com/android/repository/platform-tools-latest-$1.zip
        unzip /tmp/platform-tools.zip -d /tmp/pt
        mv /tmp/pt/platform-tools /usr/local/share/
        ln -s /usr/local/share/platform-tools/adb /usr/local/bin/adb
        ln -s /usr/local/share/platform-tools/fastboot /usr/local/bin/fastboot
    fi


    if [[ "$2" == 'Linux' ]]; then
        # install ldid
        if [ ! -x "$(command -v ldid)" ]; then
            git clone https://github.com/daeken/ldid.git /tmp/ldid
            cd /tmp/ldid
            ./make.sh
            mv ldid /usr/local/bin/
            cd /tmp
            rm -rf /tmp/ldid
        fi

        # install jtool
        if [ ! -x "$(command -v jtool)" ]; then
            curl -L -o /tmp/jtool.tar http://www.newosxbook.com/tools/jtool.tar
            mkdir /tmp/jtool
            tar xvf /tmp/jtool.tar -C /tmp/jtool
            mv /tmp/jtool/jtool.ELF64 /usr/local/bin/jtool
            rm -rf /tmp/jtool.tar /tmp/jtool
        fi

        # install other dependencies
        apt update
        apt install libimobiledevice libusbmuxd-tools usbutils

        if [ ! -x "$(command -v java)" ]; then
            apt install openjdk-10-jdk
        fi

    elif [[ "$2" == 'Darwin' ]]; then
        # checks if brew exists
        command -v brew || die "Could not find `brew` to install dependencies"
        brew update

        # iproxy, ldid
        brew install libimobiledevice ldid

        # lsusb
        brew tap jlhonora/lsusb
        brew install lsusb

        # otool
        log "Installing and accepting Xcode - Will require password"
        sudo xcode-select --install
        sudo xcodebuild -license accept
    fi

    cd $ORIGINAL_PWD;
}

function update_shrc(){
    log "Checking if /usr/local/bin in PATH"

    if [[ ! $PATH = *"/usr/local/bin"* ]]; then
        log "Adding /usr/local/bin to PATH on $1"
        echo "PATH=$PATH:/usr/local/bin" >> $1
    fi
}


install $(uname)

update_shrc $SHELL_RC