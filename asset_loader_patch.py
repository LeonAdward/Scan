#!/usr/bin/env python3
import pathlib,re,sys
root=pathlib.Path(sys.argv[1]); package='com/example/gloryofgeneralsremakeeditor'
main_files=list(root.glob('smali*/'+package+'/MainActivity.smali'))
assert len(main_files)==1, 'Expected exactly one MainActivity.smali'
main=main_files[0]; text=main.read_text()
start=text.find('.method',text.find('onCreate(')-150) if 'onCreate(' in text else -1
m=re.search(r'(?ms)^\.method[^\n]* onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method',text)
assert m, 'onCreate method not found'
method=m.group(); assert 'file:///android_asset/index.html' in method, 'Original homepage URL missing; inspect APK before patching'
method=method.replace('file:///android_asset/index.html','https://appassets.androidplatform.net/assets/index.html')
loads=list(re.finditer(r'(?m)^\s*invoke-virtual \{([vp]\d+),\s*([vp]\d+)\}, Landroid/webkit/WebView;->loadUrl\(Ljava/lang/String;\)V',method))
assert len(loads)==1, 'Expected one WebView.loadUrl call in onCreate'
reg=loads[0].group(1)
loc=re.search(r'(?m)^\s*\.locals (\d+)\s*$',method)
assert loc, 'onCreate does not use .locals; abort safely'
count=int(loc.group(1)); assert count<240
method=method[:loc.start()]+method[loc.start():loc.end()].replace(str(count),str(count+1),1)+method[loc.end():]
loads=list(re.finditer(r'(?m)^\s*invoke-virtual \{([vp]\d+),\s*([vp]\d+)\}, Landroid/webkit/WebView;->loadUrl\(Ljava/lang/String;\)V',method))
reg=loads[0].group(1); pos=loads[0].start(); temp='v'+str(count)
insert=f'''    new-instance {temp}, L{package}/ScannerAssetClient;
    invoke-direct {{{temp}, p0}}, L{package}/ScannerAssetClient;-><init>(Landroid/content/Context;)V
    invoke-virtual {{{reg}, {temp}}}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V
'''
method=method[:pos]+insert+method[pos:]
text=text[:m.start()]+method+text[m.end():];main.write_text(text)
client=main.parent/'ScannerAssetClient.smali'
assert not client.exists(), 'ScannerAssetClient already exists'
client.write_text(r'''.class public Lcom/example/gloryofgeneralsremakeeditor/ScannerAssetClient;
.super Landroid/webkit/WebViewClient;
.field private final ctx:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .locals 0
    invoke-direct {p0}, Landroid/webkit/WebViewClient;-><init>()V
    iput-object p1, p0, Lcom/example/gloryofgeneralsremakeeditor/ScannerAssetClient;->ctx:Landroid/content/Context;
    return-void
.end method

.method public shouldInterceptRequest(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Landroid/webkit/WebResourceResponse;
    .locals 1
    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;
    move-result-object v0
    invoke-virtual {p0, v0}, Lcom/example/gloryofgeneralsremakeeditor/ScannerAssetClient;->serve(Landroid/net/Uri;)Landroid/webkit/WebResourceResponse;
    move-result-object v0
    return-object v0
.end method

.method public shouldInterceptRequest(Landroid/webkit/WebView;Ljava/lang/String;)Landroid/webkit/WebResourceResponse;
    .locals 1
    invoke-static {p2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;
    move-result-object v0
    invoke-virtual {p0, v0}, Lcom/example/gloryofgeneralsremakeeditor/ScannerAssetClient;->serve(Landroid/net/Uri;)Landroid/webkit/WebResourceResponse;
    move-result-object v0
    return-object v0
.end method

.method private serve(Landroid/net/Uri;)Landroid/webkit/WebResourceResponse;
    .locals 8
    if-eqz p1, :none
    invoke-virtual {p1}, Landroid/net/Uri;->getScheme()Ljava/lang/String;
    move-result-object v0
    const-string v1, "https"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :none
    invoke-virtual {p1}, Landroid/net/Uri;->getHost()Ljava/lang/String;
    move-result-object v0
    const-string v1, "appassets.androidplatform.net"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :none
    invoke-virtual {p1}, Landroid/net/Uri;->getPath()Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :missing
    const-string v1, "/assets/"
    invoke-virtual {v0, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :missing
    const/16 v1, 0x8
    invoke-virtual {v0, v1}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v0
    const-string v1, ".."
    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-nez v1, :missing
    :try_start
    iget-object v1, p0, Lcom/example/gloryofgeneralsremakeeditor/ScannerAssetClient;->ctx:Landroid/content/Context;
    invoke-virtual {v1}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v1
    invoke-virtual {v1, v0}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v1
    const-string v2, "application/octet-stream"
    const-string v3, ".js"
    invoke-virtual {v0, v3}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3, :check_html
    const-string v2, "application/javascript"
    goto :response
    :check_html
    const-string v3, ".html"
    invoke-virtual {v0, v3}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3, :check_wasm
    const-string v2, "text/html"
    goto :response
    :check_wasm
    const-string v3, ".wasm"
    invoke-virtual {v0, v3}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3, :response
    const-string v2, "application/wasm"
    :response
    new-instance v3, Landroid/webkit/WebResourceResponse;
    const-string v4, "UTF-8"
    invoke-direct {v3, v2, v4, v1}, Landroid/webkit/WebResourceResponse;-><init>(Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)V
    return-object v3
    :try_end
    .catch Ljava/io/IOException; {:try_start .. :try_end} :missing
    :missing
    new-instance v0, Landroid/webkit/WebResourceResponse;
    const-string v1, "text/plain"
    const-string v2, "UTF-8"
    new-instance v3, Ljava/io/ByteArrayInputStream;
    const/4 v4, 0x0
    new-array v4, v4, [B
    invoke-direct {v3, v4}, Ljava/io/ByteArrayInputStream;-><init>([B)V
    invoke-direct {v0, v1, v2, v3}, Landroid/webkit/WebResourceResponse;-><init>(Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)V
    return-object v0
    :none
    const/4 v0, 0x0
    return-object v0
.end method
''')
print('HTTPS asset mapping installed:',main,client)
