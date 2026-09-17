"""Create persona dossiers by patching the retained Experiment Analysis package.
No API calls; the canonical persona data remain unchanged.
"""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from hashlib import sha256
from lxml import etree as E
import json
import re

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'selected-personas.json'
REFERENCE = Path('/Users/christophscharnagl/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-experiment-analysis/assets/reference.docx')
OUT = BASE / 'documents'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
XML = '{http://www.w3.org/XML/1998/namespace}'
TYPE = {'werkstudent':'Werkstudententätigkeit','praktikum':'Praktikum','vollzeit':'Vollzeit','teilzeit':'Teilzeit','abschlussarbeit':'Abschlussarbeit','trainee':'Trainee','ausbildung':'Ausbildung'}
REMOTE = {'onsite':'vor Ort','hybrid':'hybrid','remote':'remote'}
FOCUS = {'lernpotenzial':'Lernpotenzial','fachliche_tiefe':'Fachliche Tiefe','innovation':'Innovation','ausgewogen':'Ausgewogen'}
PRESETS = {'career_advisor':'Top-Berufsberater','top_career_advisor':'Top-Berufsberater','career':'Top-Berufsberater','domain_expert':'Fachexperte','expert':'Fachexperte','fachberater':'Fachexperte'}


def xtext(e):
    return ''.join(e.xpath('.//w:t/text()',namespaces=NS))


def val(parent, name, value):
    el=parent.find(W+name)
    if el is None: el=E.SubElement(parent,W+name)
    el.set(W+'val',str(value));return el


def clean(e):
    for el in list(e.iter()):
        for k in list(el.attrib):
            if k.endswith('}paraId') or k.endswith('}textId'):
                del el.attrib[k]
        if E.QName(el).localname in ('bookmarkStart','bookmarkEnd'):
            el.getparent().remove(el)
    return e


def newp(pattern,text,role='body',bold=False):
    p=clean(deepcopy(pattern))
    pp=p.find(W+'pPr')
    if pp is None: pp=E.Element(W+'pPr');p.insert(0,pp)
    rp0=p.find('w:r/w:rPr',NS)
    rp=deepcopy(rp0) if rp0 is not None else E.Element(W+'rPr')
    for e in list(p):
        if e is not pp: p.remove(e)
    spacing=pp.find(W+'spacing')
    if spacing is None: spacing=E.SubElement(pp,W+'spacing')
    if role=='title':
        spacing.set(W+'before','0');spacing.set(W+'after','120')
        val(rp,'sz',48);val(rp,'szCs',48);val(rp,'color','000000')
    elif role=='heading':
        val(rp,'color','000000')
    else:
        spacing.set(W+'before','80');spacing.set(W+'after','80')
        val(pp,'jc','left')
        val(pp,'widowControl',1)
        if role=='lead': val(pp,'keepNext',1)
    if bold: val(rp,'b',1);val(rp,'bCs',1)
    r=E.SubElement(p,W+'r');r.append(rp)
    t=E.SubElement(r,W+'t');t.set(XML+'space','preserve');t.text=text
    return p


def table(pattern, rows):
    t=clean(deepcopy(pattern))
    proto=deepcopy(t.find(W+'tr'))
    for tr in t.findall(W+'tr'): t.remove(tr)
    for key,value in rows:
        row=clean(deepcopy(proto))
        val(row.find(W+'trPr'),'cantSplit',1)
        for cell,txt in zip(row.findall(W+'tc'),[key,value]):
            p=cell.find(W+'p');rp=deepcopy(p.find('w:r/w:rPr',NS))
            for child in list(p):
                if child.tag!=W+'pPr':p.remove(child)
            r=E.SubElement(p,W+'r');r.append(rp)
            text=E.SubElement(r,W+'t');text.set(XML+'space','preserve');text.text=str(txt)
        t.append(row)
    return t


def serial(root):
    return E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)


def main():
    assert sha256(REFERENCE.read_bytes()).hexdigest()=='d823cd0115186b34c01c6e4b4da3be28b64ee73cac849dbd62d6f4bb6385b0fb'
    data=json.loads(SOURCE.read_text())
    cases=data.get('cases',data.get('personas'))
    assert len(cases)==6 and {c['assigned_arm'] for c in cases}=={'A','B','C'}
    assert {c['source_id'] for c in cases}=={'P01','P06'}
    execution_cases=cases
    cases=[]
    for source_id in ('P01','P06'):
        group=[c for c in execution_cases if c['source_id']==source_id]
        assert len(group)==3 and {c['assigned_arm'] for c in group}=={'A','B','C'}
        c_case=next(c for c in group if c['assigned_arm']=='C')
        person_case=deepcopy(c_case);person_case['id']=source_id
        cases.append(person_case)
    OUT.mkdir(exist_ok=True)
    manifest=[]
    with ZipFile(REFERENCE) as z:
        src={i.filename:z.read(i.filename) for i in z.infolist()}
        infos=z.infolist()
    original=E.fromstring(src['word/document.xml'])
    b=original.find(W+'body');patterns={'title':b[6],'heading':b[30],'body':b[31],'bullet':b[53],'table':b[28]}
    section=deepcopy(b[-1])
    for person in cases:
        arm='A B C'
        preferred='Top-Berufsberater'
        if isinstance(preferred,dict):
            bname=preferred.get('name') or preferred.get('label') or preferred.get('preset') or preferred.get('id')
        else: bname=PRESETS.get(preferred,preferred)
        bname=PRESETS.get(bname,bname)
        full=person['full_information_need']; initial=person['initial_profile']; advisor=person['advisor_config']
        doc=deepcopy(original);body=doc.find(W+'body');body.clear()
        def para(text,bold=False,role='body'):
            p=newp(patterns['body'],text,role,bold);body.append(p);return p
        def head(text,newpage=False):
            p=newp(patterns['heading'],text,'heading')
            if newpage:val(p.find(W+'pPr'),'pageBreakBefore',1)
            body.append(p);return p
        def field(label,text):
            para(label,True,'lead');para(text)
        def bullets(items):
            for item in items:body.append(newp(patterns['bullet'],item,'bullet'))
        def fields(rows):body.append(table(patterns['table'],rows))

        body.append(newp(patterns['title'],person['name'],'title'))
        para(f"Persona {person['id']}   |   Varianten A B C   |   17. September 2026",bold=True)
        para('Diese vollständig fiktive Person durchläuft DIANA in den Varianten A, B und C. Jede Sitzung beginnt mit demselben Profil und umfasst eine Suche sowie drei Nachrichten. Der Fall prüft die Entwicklung der Rangfolgen im Gespräch; er ist keine echte Studienteilnahme.')
        fields([('Fall',person['id']),('Alter',f"{person['age']} Jahre"),('Gruppe',person['group'])])
        head('Hintergrund und Ausbildung')
        para(person['biography']);para(person['education'])
        field('Bisherige Erfahrung',' '.join(person['experience']))
        head('Kenntnisse und Grenzen')
        field('Vorhandene Kenntnisse',', '.join(person['skills']))
        field('Noch nicht belegt',' '.join(person['limitations']))

        head('Suchbedarf und Startprofil',True)
        para(person['job_goal'])
        field('Zulässige Stellenarten',', '.join(TYPE.get(t,t) for t in person['employment_types']))
        field('Passende Aufgaben', '; '.join(full['relevant_task_families']))
        para('Prioritäten in dieser Reihenfolge',True,'lead')
        for i,v in enumerate(full['ordered_priorities'],1):para(f'{i}. {v}')
        field('Weiche Rahmenwünsche',f"Orte: {', '.join(full['locations'])}. Arbeitsmodell: {', '.join(REMOTE.get(r,r) for r in full['remote'])}. Gewünschter maximaler Umfang: {full['max_hours']:g} Stunden pro Woche.")
        head('Eingaben bei der Profilerstellung')
        field('Suchwunsch',initial['query'])
        field('Kenntnisse',', '.join(initial['skills']))
        field('Anfängliche Wünsche','; '.join(initial['preferences']))
        field('Lebenslauftext',initial['cv_text'])
        para('Im Startprofil werden nur die oben genannten Stellenarten ausgewählt. Ort, Arbeitsmodell und Stunden bleiben in den Filterfeldern zunächst leer. Die im Gespräch genannten Details sind Teil des vorab definierten Suchbedarfs.')

        head('Beratung in A B und C',True)
        para(f'A nutzt die feste Standardberatung. In B wird die Vorlage {bname} unverändert ausgewählt. In C wird die Beratung selbst gestaltet. Suchbedarf und Fähigkeiten bleiben in allen Varianten gleich; jede Variante erhält eine eigene Sitzung.')
        para(f"Eigene Beratung in C: {advisor['name']}. Eigenschaften: {', '.join(advisor['traits'])}. Bewertungsfokus: {FOCUS.get(advisor['focus'],advisor['focus'])}.")
        field('Eigener Hinweis in C',advisor['description'])
        head('Drei geplante Gesprächsetappen')
        para('Die Informationsetappen sind für A, B und C gleich. Codex formuliert die tatsächlichen Nachrichten passend zur vorherigen Antwort. Fakten und Suchziel stehen vorher fest. Die Texte unten sind Formulierungsgrundlagen, keine bereits geführten Gespräche.')
        for msg in person['disclosure_plan']:
            para(f"Etappe {msg['turn']}",True,'lead')
            para(msg['message'])
            para('Informationsziel: '+msg['fact_or_priority'])
        para('Die Formulierungsgrundlagen sind keine behaupteten Gesprächsverläufe. Tatsächlich gesendete Nachrichten, Antworten und die danach vorliegenden Rangfolgen werden separat protokolliert.')

        head('Konstanter Bewertungsmaßstab',True)
        para('Der vollständige Suchbedarf dieses Dokuments ist der feste Maßstab für alle Rangfolgen. Bewertet wird, ob die Gespräche die Empfehlungen an diesen bereits bestehenden Bedarf annähern.')
        para(full['evidence_policy'])
        for grade,rule in person['evaluation_relevance_rules'].items():
            field(f'Relevanzstufe {grade}',rule)
        para('Für Precision und MRR gelten die Stufen 2 und 3 als relevant. nDCG verwendet alle vier Relevanzstufen. Bewertet werden die Stellenanzeige und dieses Profil; der Systemscore und die vom System erzeugte Begründung gelten nicht als Referenzurteil.')
        head('Messpunkte und Kennzahlen')
        para('Messpunkte in A, B und C: erste Suche sowie nach Nachricht 1, 2 und 3. Kennzahlen: nDCG@10, nDCG@5, Precision@5 und MRR@10. Die Referenzmenge vereinigt die bis zu 20 Ergebnisstellen je Messpunkt. Alle zwölf Rangfolgen dieser Person nutzen denselben idealen Pool.')
        para('Die Relevanzbewertung stammt vom Codex-Assistenten. Zwei fiktive Fälle liefern keinen verallgemeinerbaren Wirksamkeitsnachweis und ersetzen keine Nutzerurteile. Zufriedenheit und tatsächliche Bewerbungschancen werden nicht gemessen.')
        body.append(deepcopy(section))

        footer=E.fromstring(src['word/footer1.xml'])
        for t in footer.xpath('.//w:t',namespaces=NS):
            if t.text=='Report Name':t.text=f"DIANA  |  {person['id']}  |  {person['name']}"
        settings=E.fromstring(src['word/settings.xml']);val(settings,'updateFields','true')
        changed={'word/document.xml':serial(doc),'word/footer1.xml':serial(footer),'word/settings.xml':serial(settings)}
        filename=f"{person['id']}-{person['name'].lower().replace(' ','-')}.docx"
        target=OUT/filename
        with ZipFile(target,'w') as zz:
            for info in infos:zz.writestr(info,changed.get(info.filename,src[info.filename]))
        with ZipFile(target) as zz:
            unchanged=[name for name,blob in src.items() if name not in changed and blob==zz.read(name)]
            assert len(unchanged)==len(src)-3
            raw=E.fromstring(zz.read('word/document.xml'))
            texts=raw.xpath('.//w:t/text()',namespaces=NS)
            assert all(any(m in text for text in texts) for m in person['planned_messages'])
            assert initial['query'] in texts and initial['cv_text'] in texts
            assert advisor['description'] in texts
            assert raw.xpath('count(.//w:sectPr)',namespaces=NS)==1
        manifest.append({'id':person['id'],'name':person['name'],'file':filename,'sha256':sha256(target.read_bytes()).hexdigest(),'persona_source_sha256':sha256(SOURCE.read_bytes()).hexdigest(),'preserved_parts':unchanged,'modified_parts':list(changed),'assigned_arms':['A','B','C'],'b_template':bname,'execution_ids':[c['id'] for c in execution_cases if c['source_id']==person['id']]})
    (OUT/'document-manifest.json').write_text(json.dumps({'reference_sha256':sha256(REFERENCE.read_bytes()).hexdigest(),'scope_change':'User changed the requested deliverables from twelve to two persona dossiers across three systems after the create-operation marker; marker not repeated.','documents':manifest},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'documents':len(manifest),'output':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
