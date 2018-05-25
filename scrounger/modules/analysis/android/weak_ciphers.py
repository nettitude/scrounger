from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import smali_dirs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application is using deprecated ciphers",
        "certainty": 100
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        }
    ]

    file_regex = r"javax.net.ssl.SSLSocket"
    regex = r"SSL_DHE_DSS_EXPORT_WITH_DES40_CBC_SHA|\
SSL_DHE_DSS_WITH_3DES_EDE_CBC_SHA|SSL_DHE_DSS_WITH_DES_CBC_SHA|\
SSL_DHE_RSA_EXPORT_WITH_DES40_CBC_SHA|SSL_DHE_RSA_WITH_3DES_EDE_CBC_SHA|\
SSL_DHE_RSA_WITH_DES_CBC_SHA|SSL_DH_anon_EXPORT_WITH_DES40_CBC_SHA|\
SSL_DH_anon_EXPORT_WITH_RC4_40_MD5|SSL_DH_anon_WITH_3DES_EDE_CBC_SHA|\
SSL_DH_anon_WITH_DES_CBC_SHA|SSL_DH_anon_WITH_RC4_128_MD5|\
SSL_RSA_EXPORT_WITH_DES40_CBC_SHA|SSL_RSA_EXPORT_WITH_RC4_40_MD5|\
SSL_RSA_WITH_DES_CBC_SHA|SSL_RSA_WITH_NULL_MD5|SSL_RSA_WITH_NULL_SHA|\
SSL_RSA_WITH_RC4_128_MD5|SSL_RSA_WITH_RC4_128_SHA|\
TLS_DHE_DSS_WITH_AES_128_CBC_SHA|TLS_DHE_DSS_WITH_AES_128_CBC_SHA256|\
TLS_DHE_DSS_WITH_AES_128_GCM_SHA256|TLS_DHE_DSS_WITH_AES_256_CBC_SHA|\
TLS_DHE_DSS_WITH_AES_256_CBC_SHA256|TLS_DHE_DSS_WITH_AES_256_GCM_SHA384|\
TLS_DHE_RSA_WITH_AES_128_CBC_SHA|TLS_DHE_RSA_WITH_AES_128_CBC_SHA256|\
TLS_DHE_RSA_WITH_AES_128_GCM_SHA256|TLS_DHE_RSA_WITH_AES_256_CBC_SHA|\
TLS_DHE_RSA_WITH_AES_256_CBC_SHA256|TLS_DHE_RSA_WITH_AES_256_GCM_SHA384|\
TLS_DH_anon_WITH_AES_128_CBC_SHA|TLS_DH_anon_WITH_AES_128_CBC_SHA256|\
TLS_DH_anon_WITH_AES_128_GCM_SHA256|TLS_DH_anon_WITH_AES_256_CBC_SHA|\
TLS_DH_anon_WITH_AES_256_CBC_SHA256|TLS_DH_anon_WITH_AES_256_GCM_SHA384|\
TLS_ECDHE_ECDSA_WITH_3DES_EDE_CBC_SHA|TLS_ECDHE_ECDSA_WITH_NULL_SHA|\
TLS_ECDHE_ECDSA_WITH_RC4_128_SHA|TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA|\
TLS_ECDHE_RSA_WITH_NULL_SHA|TLS_ECDHE_RSA_WITH_RC4_128_SHA|\
TLS_ECDH_ECDSA_WITH_3DES_EDE_CBC_SHA|TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA|\
TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA256|TLS_ECDH_ECDSA_WITH_AES_128_GCM_SHA256|\
TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA|TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA384|\
TLS_ECDH_ECDSA_WITH_AES_256_GCM_SHA384|TLS_ECDH_ECDSA_WITH_NULL_SHA|\
TLS_ECDH_ECDSA_WITH_RC4_128_SHA|TLS_ECDH_RSA_WITH_3DES_EDE_CBC_SHA|\
TLS_ECDH_RSA_WITH_AES_128_CBC_SHA|TLS_ECDH_RSA_WITH_AES_128_CBC_SHA256|\
TLS_ECDH_RSA_WITH_AES_128_GCM_SHA256|TLS_ECDlH_RSA_WITH_AES_256_CBC_SHA|\
TLS_ECDH_RSA_WITH_AES_256_CBC_SHA384|TLS_ECDH_RSA_WITH_AES_256_GCM_SHA384|\
TLS_ECDH_RSA_WITH_NULL_SHA|TLS_ECDH_RSA_WITH_RC4_128_SHA|\
TLS_ECDH_anon_WITH_3DES_EDE_CBC_SHA|TLS_ECDH_anon_WITH_AES_128_CBC_SHA|\
TLS_ECDH_anon_WITH_AES_256_CBC_SHA|TLS_ECDH_anon_WITH_NULL_SHA|\
TLS_ECDH_anon_WITH_RC4_128_SHA|TLS_PSK_WITH_3DES_EDE_CBC_SHA|\
TLS_PSK_WITH_RC4_128_SHA|TLS_RSA_WITH_NULL_SHA256|SSL_RSA_WITH_DES_CBC_SHA|\
TLS_DHE_DSS_WITH_AES_128_CBC_SHA|TLS_DHE_DSS_WITH_AES_256_CBC_SHA|\
SSL_DHE_DSS_WITH_DES_CBC_SHA|SSL_DHE_DSS_WITH_3DES_EDE_CBC_SHA|\
SSL_DHE_RSA_WITH_DES_CBC_SHA|SSL_DHE_RSA_WITH_3DES_EDE_CBC_SHA|\
SSL_RSA_EXPORT_WITH_DES40_CBC_SHA|SSL_DHE_DSS_EXPORT_WITH_DES40_CBC_SHA|\
SSL_DHE_RSA_EXPORT_WITH_DES40_CBC_SHA|SSL_RSA_EXPORT_WITH_RC4_40_MD5|\
SSL_RSA_WITH_RC4_128_MD5|SSL_RSA_WITH_RC4_128_SHA"

    def run(self):
        result = {
            "title": "Application Uses Deprecated Ciphers",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # preparing variable to run
        ciphers = []
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            ssl_socket_files = pretty_grep(self.file_regex, smali)
            ciphers += pretty_grep(self.regex, smali)

        if ciphers:
            result.update({
                "report": True,
                "details": pretty_grep_to_str(
                    ciphers, self.decompiled_apk, ignore)
            })

        return {
            "{}_result".format(self.name()): result
        }

    """ Getting Ciphers
    import requests
    from BeautifulSoup import BeautifulSoup
    url = "https://developer.android.com/reference/javax/net/ssl/SSLSocket.html"
    a = requests.get(url)
    s = BeautifulSoup(a.text)
    trs = s.findAll('tr', attrs={'class': 'deprecated'})
    for i in trs:
        tds = i.findAll('td')
        print tds[1].text if len(tds) == 4 else tds[0].text
    """
