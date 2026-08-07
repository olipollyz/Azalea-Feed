import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_changelog(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    updates = []
    current_update = None
    current_category = None
    
    # regex for version and date e.g. ## [v0.4.0] - 2025-10-15
    version_re = re.compile(r'^##\s+\[?(v?\d+\.\d+\.\d+)\]?(?:\s+-\s+(\d{4}-\d{2}-\d{2}))?')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        v_match = version_re.match(line)
        if v_match:
            if current_update:
                updates.append(current_update)
            version = v_match.group(1)
            date = v_match.group(2) if v_match.group(2) else ""
            current_update = {
                "id": f"update-{version.replace('.', '-')}",
                "version": version,
                "date": date,
                "title": f"Update {version}",
                "description": "",
                "changes": {
                    "added": [],
                    "changed": [],
                    "fixed": [],
                    "removed": []
                }
            }
            current_category = None
            continue
            
        if current_update:
            if line.startswith('###'):
                cat = line.strip('# ').lower()
                if cat in current_update["changes"]:
                    current_category = cat
            elif line.startswith('-') or line.startswith('*'):
                if current_category:
                    item = line.lstrip('-* ').strip()
                    current_update["changes"][current_category].append(item)
                else:
                    # If it's outside a category, it might be the description
                    current_update["description"] += line.lstrip('-* ') + " "
            elif not line.startswith('#'):
                current_update["description"] += line + " "

    if current_update:
        updates.append(current_update)
        
    for u in updates:
        u["description"] = u["description"].strip()
        
    return updates

def build_json(updates, out_path):
    out_data = {"updates": []}
    for u in updates:
        out_update = {
            "id": u["id"],
            "version": u["version"],
            "date": u["date"],
            "title": u["title"],
            "description": u["description"],
            "changes": {}
        }
        for k, v in u["changes"].items():
            if v:
                out_update["changes"][k] = v
        out_data["updates"].append(out_update)
        
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2)

def build_xml(updates, out_path):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Azalea Changelog Feed"
    ET.SubElement(channel, "link").text = "https://github.com/olipollyz/Azalea-Feed"
    ET.SubElement(channel, "description").text = "Updates for Azalea DayZ Map"
    
    for u in updates:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"Azalea {u['version']} - {u['date']}"
        ET.SubElement(item, "guid").text = u['id']
        ET.SubElement(item, "pubDate").text = u['date']
        
        desc = u['description'] + "\n"
        for k, v in u['changes'].items():
            if v:
                desc += f"\n### {k.capitalize()}\n"
                for i in v:
                    desc += f"- {i}\n"
        
        ET.SubElement(item, "description").text = desc
        
    tree = ET.ElementTree(rss)
    tree.write(out_path, encoding='utf-8', xml_declaration=True)

def build_txt(updates, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for u in updates:
            f.write(f"Update {u['version']} - {u['date']}\n")
            f.write("="*40 + "\n\n")
            if u['description']:
                f.write(f"{u['description']}\n\n")
            
            for cat, items in u['changes'].items():
                if items:
                    f.write(f"[{cat.upper()}]\n")
                    for item in items:
                        prefix = "-" if cat == "removed" or cat == "fixed" else "+"
                        f.write(f"{prefix} {item}\n")
                    f.write("\n")
            f.write("\n")

if __name__ == "__main__":
    import sys
    changelog_path = "CHANGELOG.md"
    updates = parse_changelog(changelog_path)
    build_json(updates, "changelog.json")
    build_xml(updates, "feed.xml")
    build_txt(updates, "changelog.txt")
    print(f"Successfully built changelog.json, feed.xml, and changelog.txt from {len(updates)} releases.")
