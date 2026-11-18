#!/usr/bin/env python3
import os,re,sys,pathlib,xml.etree.ElementTree as ET
root=pathlib.Path(sys.argv[1]); android='{http://schemas.android.com/apk/res/android}'
manifest=root/'AndroidManifest.xml'; tree=ET.parse(manifest); m=tree.getroot()
ET.register_namespace('android','http://schemas.android.com/apk/res/android')
if not any(e.get(android+'name')=='android.permission.CAMERA' for e in m.findall('uses-permission')):
    e=ET.Element('uses-permission'); e.set(android+'name','android.permission.CAMERA'); m.insert(0,e)
app=m.find('application')
for a in app.findall('.//activity'):
    if 'MainActivity' in a.get(android+'name',''):
        a.set(android+'screenOrientation','portrait')
tree.write(manifest,encoding='utf-8',xml_declaration=True)
main_files=list(root.glob('smali*/com/example/gloryofgeneralsremakeeditor/MainActivity.smali'))
chrome_files=list(root.glob('smali*/com/example/gloryofgeneralsremakeeditor/MainActivity$1.smali'))
assert len(main_files)==1 and len(chrome_files)==1, 'Cannot locate unique MainActivity and WebChromeClient; abort'
main=main_files[0]; chrome=chrome_files[0]; s=main.read_text(); c=chrome.read_text()
assert '.method' in s and 'Landroid/webkit/WebChromeClient;' in c and 'this$0:Lcom/example/gloryofgeneralsremakeeditor/MainActivity;' in c, 'Unexpected DEX class layout'
# Inject immediately after onCreate super call; no extra register consumption.
pattern=r'(?ms)(\.method[^\n]* onCreate\(Landroid/os/Bundle;\)V\n.*?invoke-super \{[^\n]*\}, [^\n]*->onCreate\(Landroid/os/Bundle;\)V)'
match=re.search(pattern,s)
assert match, 'Cannot find onCreate invoke-super; abort rather than produce unpatched APK'
s=s[:match.end()]+ '\n    invoke-static {p0}, Lcom/example/gloryofgeneralsremakeeditor/MainActivity;->ensureCameraPermission(Landroid/app/Activity;)V'+s[match.end():]
helper='''
.method public static ensureCameraPermission(Landroid/app/Activity;)V
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

.method public static grantCameraRequest(Landroid/app/Activity;Landroid/webkit/PermissionRequest;)V
    .locals 5
    # Grant only VIDEO_CAPTURE and only for file: or appassets.androidplatform.net HTTPS origin.
    invoke-virtual {p1}, Landroid/webkit/PermissionRequest;->getOrigin()Landroid/net/Uri;
    move-result-object v0
    if-eqz v0, :deny
    invoke-virtual {v0}, Landroid/net/Uri;->getScheme()Ljava/lang/String;
    move-result-object v1
    const-string v2, "file"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-nez v2, :origin_ok
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
    const-string v0, "android.permission.CAMERA"
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x17
    if-lt v1, v2, :check_resources
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
s+='\n'+helper
# Existing anonymous WebChromeClient receives an additional override.
assert 'onPermissionRequest(Landroid/webkit/PermissionRequest;)V' not in c, 'Existing permission callback; abort'
c+='''
.method public onPermissionRequest(Landroid/webkit/PermissionRequest;)V
    .locals 1
    iget-object v0, p0, Lcom/example/gloryofgeneralsremakeeditor/MainActivity$1;->this$0:Lcom/example/gloryofgeneralsremakeeditor/MainActivity;
    invoke-static {v0, p1}, Lcom/example/gloryofgeneralsremakeeditor/MainActivity;->grantCameraRequest(Landroid/app/Activity;Landroid/webkit/PermissionRequest;)V
    return-void
.end method
'''
main.write_text(s);chrome.write_text(c)
js=root/'assets/scanner.js'; source=pathlib.Path(sys.argv[2]); assert js.exists(), 'scanner.js not found in APK'; js.write_bytes(source.read_bytes())
# Offline-first server connector; no network traffic until explicitly enabled.
for asset in ['server-config.js','server-client.js']:
    (root/'assets'/asset).write_bytes((source.parent/asset).read_bytes())
htmls=list((root/'assets').glob('*.html'))
if htmls:
    html=next((x for x in htmls if x.name=='index.html'),htmls[0]); h=html.read_text(encoding='utf-8')
    if 'server-client.js' not in h:
        insert='<script src="server-config.js"></script><script src="server-client.js"></script>'
        h=h.replace('</head>',insert+'</head>') if '</head>' in h else h.replace('</body>',insert+'</body>')
        html.write_text(h,encoding='utf-8')
print('Added future server connector (disabled by default)')
print('Patched',main,chrome,manifest,js)
