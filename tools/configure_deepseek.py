"""Configure a local Windows DPAPI-encrypted DeepSeek key; never print it."""
import ctypes
from ctypes import wintypes
import getpass
import os
from pathlib import Path


class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]


def key_path():return Path(os.environ['LOCALAPPDATA'])/'TempoEvo'/'deepseek.key.dpapi'


def crypt(value,decrypt=False):
    if os.name!='nt':raise RuntimeError('Use the DEEPSEEK_API_KEY environment variable on Linux')
    buffer=ctypes.create_string_buffer(value);source=Blob(len(value),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
    library=ctypes.WinDLL('crypt32',use_last_error=True)
    library.CryptProtectData.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    library.CryptUnprotectData.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    library.CryptProtectData.restype=library.CryptUnprotectData.restype=wintypes.BOOL
    if decrypt:ok=library.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target))
    else:ok=library.CryptProtectData(ctypes.byref(source),'TempoEvo DeepSeek',None,None,None,1,ctypes.byref(target))
    if not ok:raise ctypes.WinError(ctypes.get_last_error())
    try:return ctypes.string_at(target.data,target.size)
    finally:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.LocalFree.argtypes=[ctypes.c_void_p]
        kernel.LocalFree(ctypes.cast(target.data,ctypes.c_void_p))


def load_key():
    if os.environ.get('DEEPSEEK_API_KEY'):return os.environ['DEEPSEEK_API_KEY']
    if os.name=='nt' and key_path().is_file():return crypt(key_path().read_bytes(),True).decode('utf8')
    raise RuntimeError('DeepSeek key is not configured locally; run tools/configure_deepseek.py')


if __name__=='__main__':
    value=getpass.getpass('请粘贴 DeepSeek API key（输入不会显示），然后回车：').strip()
    if not value.startswith('sk-') or len(value)<16:raise SystemExit('格式不正确。请重新运行；不要把 key 发到聊天里。')
    target=key_path();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(crypt(value.encode('utf8')))
    print('已保存到本机当前 Windows 用户的加密凭据文件。没有调用模型，也没有修改 Codex 全局配置。')
