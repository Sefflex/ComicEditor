"""
dist/ComicEditor klasöründen WiX v4 uyumlu HarvestedFiles.wxs üretir.
Kullanim: python generate_harvest.py <source_dir> <output_wxs>
"""
import os
import sys
import hashlib
from pathlib import Path


def make_id(*parts):
    combined = '_'.join(str(p) for p in parts)
    h = hashlib.md5(combined.encode()).hexdigest()[:8]
    safe = ''.join(c if c.isalnum() else '_' for c in combined)[:28]
    return f'id_{safe}_{h}'


def generate(source_dir, output_file, component_group='ApplicationFiles', dir_ref='INSTALLFOLDER'):
    source_path = Path(source_dir).resolve()
    lines = []
    comp_ids = []

    def walk(current_path, rel_path, indent):
        entries = sorted(os.listdir(current_path))
        files = [e for e in entries if os.path.isfile(current_path / e)]
        dirs  = [e for e in entries if os.path.isdir(current_path / e)]

        for fname in files:
            file_rel = (rel_path / fname) if str(rel_path) != '.' else Path(fname)
            cid = make_id('comp', str(file_rel))
            fid = make_id('file', str(file_rel))
            src = str(file_rel).replace('/', '\\')
            lines.append(f'{indent}<Component Id="{cid}" Guid="*">')
            lines.append(f'{indent}  <File Id="{fid}" Source="$(var.SourceDir)\\{src}" KeyPath="yes" />')
            lines.append(f'{indent}</Component>')
            comp_ids.append(cid)

        for dname in dirs:
            sub_rel = (rel_path / dname) if str(rel_path) != '.' else Path(dname)
            did = make_id('dir', str(sub_rel))
            lines.append(f'{indent}<Directory Id="{did}" Name="{dname}">')
            walk(current_path / dname, sub_rel, indent + '  ')
            lines.append(f'{indent}</Directory>')

    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">',
        '  <Fragment>',
        f'    <DirectoryRef Id="{dir_ref}">',
    ]
    walk(source_path, Path('.'), '      ')
    footer_dir = [
        '    </DirectoryRef>',
        f'    <ComponentGroup Id="{component_group}">',
    ]
    comp_refs = [f'      <ComponentRef Id="{cid}" />' for cid in comp_ids]
    footer = [
        '    </ComponentGroup>',
        '  </Fragment>',
        '</Wix>',
    ]

    all_lines = header + lines + footer_dir + comp_refs + footer
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_lines) + '\n')

    print(f"Olusturuldu: {output_file}  ({len(comp_ids)} dosya)")


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else r'dist\ComicEditor'
    out = sys.argv[2] if len(sys.argv) > 2 else r'installer\HarvestedFiles.wxs'
    generate(src, out)
