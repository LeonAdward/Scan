#!/usr/bin/env python3
"""V19 camera permission patch for the verified V17 MainActivity APK."""
import pathlib, re, sys, zipfile, xml.etree.ElementTree as ET
root=pathlib.Path(sys.argv[1])
android='{http://schemas.android.com/apk/res/android}'
manifest=root/'AndroidManifest.xml'; ET.register_namespace('android','http://schemas.android.com/apk/res/android')
tree=ET.parse(manifest); m=tree.getroot()
if not any(x.get(android+'name')=='android.permission.CAMERA' for x in m.findall('uses-permission')):
    e=ET.Element('uses-permission');e.set(android+'name','android.permission.CAMERA');m.insert(0,e)
tree.write(manifest,encoding='utf-8',xml_declaration=True)
main=list(root.glob('smali*/com/example/gloryofgeneralsremakeeditor/MainActivity.smali'))
chrome=list(root.glob('smali*/com/example/gloryofgeneralsremakeeditor/MainActivity$1.smali'))
if len(main)!=1 or len(chrome)!=1: raise SystemExit('Unexpected MainActivity/WebChromeClient class structure')
p=main[0];s=p.read_text();c=chrome[0].read_text()
if 'v17EnableJavaScript' not in s: raise SystemExit('V17 JS fix missing: refusing to patch wrong APK')
if 'v19EnsureCamera' in s or 'onPermissionRequest(Landroid/webkit/PermissionRequest;)V' in c: raise SystemExit('Camera patch already present: refusing duplicate')
# Camera permission is requested on launch; no existing registers consumed.
pat=r'(\.method[^\n]* onCreate\(Landroid/os/Bundle;\)V\n.*?invoke-super \{[^\n]*\}, [^\n]*->onCreate\(Landroid/os/Bundle;\)V)'
matches=list(re.finditer(pat,s,re.S))
if len(matches)!=1: raise SystemExit('Could not identify onCreate super invocation')
m0=matches[0];s=s[:m0.end()]+'\n    invoke-static {p0}, Lcom/example/gloryofgeneralsremakeeditor/MainActivity;->v19EnsureCamera(Landroid/app/Activity;)V'+s[m0.end():]
s+='''
.method public static v19EnsureCamera(Landroid/app/Activity;)V
    .locals 3
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x17
    if-lt v0, v1, :done
    const-string v0, "android.permission.CAMERA"
    invoke-virtual {p0, v0}, Landroid/app/Activity;->checkSelfPermission(Ljava/lang/String;)I
    move-result v1
    if-eqz v1, :done
    const/4 v1, 0x1
    new-array v1, v1, [Ljava/lang/String;
    const/4 v2, 0x0
    aput-object v0, v1, v2
    const/16 v0, 0x2bd
    invoke-virtual {p0, v1, v0}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V
  :done
    return-void
.end method

.method public static v19GrantCamera(Landroid/app/Activity;Landroid/webkit/PermissionRequest;)V
    .locals 5
    invoke-virtual {p1}, Landroid/webkit/PermissionRequest;->getOrigin()Landroid/net/Uri;
    move-result-object v0
    if-eqz v0, :deny
    invoke-virtual {v0}, Landroid/net/Uri;->getScheme()Ljava/lang/String;
    move-result-object v1
    const-string v2, "file"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :check_https
    invoke-virtual {v0}, Landroid/net/Uri;->getPath()Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :deny
    const-string v2, "/android_asset/"
    invoke-virtual {v1, v2}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v2
    if-eqz v2, :deny
    goto :origin_ok
  :check_https
    const-string v2, "https"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :deny
    invoke-virtual {v0}, Landroid/net/Uri;->getHost()Ljava/lang/String;
    move-result-object v1
    const-string v2, "appassets.androidplatform.net"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :deny
  :origin_ok
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x17
    if-lt v0, v1, :check_resources
    const-string v0, "android.permission.CAMERA"
    invoke-virtual {p0, v0}, Landroid/app/Activity;->checkSelfPermission(Ljava/lang/String;)I
    move-result v1
    if-nez v1, :deny
  :check_resources
    invoke-virtual {p1}, Landroid/webkit/PermissionRequest;->getResources()[Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :deny
    array-length v1, v0
    const/4 v2, 0x0
  :loop
    if-ge v2, v1, :deny
    aget-object v3, v0, v2
    const-string v4, "android.webkit.resource.VIDEO_CAPTURE"
    invoke-virtual {v4, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-nez v3, :grant
    add-int/lit8 v2, v2, 0x1
    goto :loop
  :grant
    const/4 v0, 0x1
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "android.webkit.resource.VIDEO_CAPTURE"
    aput-object v2, v0, v1
    invoke-virtual {p1, v0}, Landroid/webkit/PermissionRequest;->grant([Ljava/lang/String;)V
    return-void
  :deny
    invoke-virtual {p1}, Landroid/webkit/PermissionRequest;->deny()V
    return-void
.end method
'''
c+='''
.method public onPermissionRequest(Landroid/webkit/PermissionRequest;)V
    .locals 1
    iget-object v0, p0, Lcom/example/gloryofgeneralsremakeeditor/MainActivity$1;->this$0:Lcom/example/gloryofgeneralsremakeeditor/MainActivity;
    invoke-static {v0, p1}, Lcom/example/gloryofgeneralsremakeeditor/MainActivity;->v19GrantCamera(Landroid/app/Activity;Landroid/webkit/PermissionRequest;)V
    return-void
.end method
'''
p.write_text(s);chrome[0].write_text(c)
# Use files already present in the GitHub repository.
assets=pathlib.Path('assets')
for n in ('index.html','scanner.js','ocr.js','ocr/tesseract.min.js','ocr/worker.min.js','ocr/lang/eng.traineddata.gz'):
    assert (assets/n).is_file(), f'Missing existing repository asset: {n}'
import shutil
shutil.copytree(assets,root/'assets',dirs_exist_ok=True)
assert 'getUserMedia' in (root/'assets/scanner.js').read_text()
print('V19 camera native patch and existing scanner assets applied')
