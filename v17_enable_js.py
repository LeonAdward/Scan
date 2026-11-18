#!/usr/bin/env python3
import pathlib,re,sys
root=pathlib.Path(sys.argv[1])
files=list(root.glob('smali*/com/example/gloryofgeneralsremakeeditor/MainActivity.smali'))
if len(files)!=1: raise SystemExit('ERROR: MainActivity.smali not unique')
p=files[0];s=p.read_text()
# Enable JavaScript immediately before loading the initial WebView URL. No new registers are consumed.
pat=r'(?m)^(\s*)invoke-virtual \{([vp]\d+),\s*([vp]\d+)\}, Landroid/webkit/WebView;->loadUrl\(Ljava/lang/String;\)V'
matches=list(re.finditer(pat,s))
if len(matches)!=1: raise SystemExit(f'ERROR: expected exactly one WebView.loadUrl call; found {len(matches)}. Refusing unsafe patch.')
m=matches[0]; indent=m.group(1); receiver=m.group(2)
insert=f'{indent}invoke-static {{{receiver}}}, Lcom/example/gloryofgeneralsremakeeditor/MainActivity;->v17EnableJavaScript(Landroid/webkit/WebView;)V\n'
s=s[:m.start()]+insert+s[m.start():]
helper='''
.method public static v17EnableJavaScript(Landroid/webkit/WebView;)V
    .locals 2
    invoke-virtual {p0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v0
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    return-void
.end method
'''
if 'v17EnableJavaScript' not in s: raise SystemExit('ERROR: insertion failed')
p.write_text(s+'\n'+helper)
print('V17 JavaScript enabled before WebView.loadUrl; smali patch written')
