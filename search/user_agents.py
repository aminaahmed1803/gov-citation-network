import random

def get_useragent():
    """
    Randomly returns either:
    - A Lynx-based string (as before), or
    - A realistic Chrome desktop UA.
    """
    if random.random() < 0.5:
        # existing Lynx-based UA
        lynx = f"Lynx/{random.randint(2,3)}.{random.randint(8,9)}.{random.randint(0,2)}"
        libwww = f"libwww-FM/{random.randint(2,3)}.{random.randint(13,15)}"
        sslmm = f"SSL-MM/{random.randint(1,2)}.{random.randint(3,5)}"
        openssl = f"OpenSSL/{random.randint(1,3)}.{random.randint(0,4)}.{random.randint(0,9)}"
        return f"{lynx} {libwww} {sslmm} {openssl}"
    else:
        # realistic Chrome UA on Windows
        major = random.randint(80,115)
        build = random.randint(4000,6000)
        patch = random.randint(0,200)
        return (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{major}.0.{build}.{patch} Safari/537.36"
        )

